#!/usr/bin/env python3
"""
Sync blockchain transactions → blockchain_history and recalculate account balances.

Run: docker exec bot python3 /app/wallet_sync.py

Env:
    LISTENER_API_URL   URL cleanroom-watcher (default: http://localhost:8080)
    LISTENER_API_KEY   API key, if required
    LISTENER_NETWORK   Network (default: tron)

Balance logic:
    account.amount = SUM(blockchain_history.count) over all wallets of the account.
    IN transactions → +amount, OUT → -amount. The balance is recalculated after all wallets
    of the account are synced, even if there were no new transactions.
"""

import asyncio
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Optional

import aiohttp
from dotenv import load_dotenv
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from db.engine import get_engine
from db.models.account import Account
from db.models.account_wallet import AccountWallet
from db.models.blockchain_history import BlockchainHistory
from db.query.account_wallet import get_all_wallets_with_accounts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [wallet_sync] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

API_URL = os.getenv("LISTENER_API_URL", "http://localhost:8080").rstrip("/")
API_KEY = os.getenv("LISTENER_API_KEY", "")
# Fallback network if a wallet has none set
NETWORK = os.getenv("LISTENER_NETWORK", "tron")


async def fetch_page(
    http: aiohttp.ClientSession,
    address: str,
    network: str,
    page: int = 1,
    per_page: int = 50,
    sort: str = "asc",
) -> tuple[Optional[list], dict]:
    """Fetch one page of transactions.
    Returns (None, {}) if the address is not found (404), ([], {}) on a network error.
    """
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    url = f"{API_URL}/api/addresses/{address}/transactions"
    params = {"network": network, "per_page": per_page, "page": page, "sort": sort}
    try:
        async with http.get(url, params=params, headers=headers,
                            timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 404:
                return None, {}
            resp.raise_for_status()
            data = await resp.json()
            pagination = {
                "pages": data.get("pages", 1),
                "total": data.get("total", 0),
            }
            return data.get("items", []), pagination
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.error("request failed %s page %d: %s", address, page, e)
        return [], {}


async def known_txids(session: AsyncSession, wallet_id) -> set:
    result = await session.execute(
        select(BlockchainHistory.txid).where(BlockchainHistory.wallet_id == wallet_id)
    )
    return {row[0] for row in result.fetchall()}


def _save_tx(session: AsyncSession, wallet: AccountWallet, account, tx: dict, seen: set) -> bool:
    """Add a transaction to the session. Returns True if it was added."""
    txid = tx.get("txid", "")
    if not txid or txid in seen:
        return False
    amount = float(tx.get("amount") or 0)
    direction = tx.get("direction", "IN")
    count = amount if direction == "IN" else -amount
    ts = tx.get("ts", "")
    try:
        time = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        time = datetime.utcnow()
    session.add(BlockchainHistory(
        account_id=account.id,
        group_id=account.group_id,
        wallet_id=wallet.id,
        wallet_address=wallet.wallet_address,
        currency=tx.get("currency") or account.currency,
        count=count,
        comment=txid,
        time=time,
        txid=txid,
    ))
    seen.add(txid)
    log.info("  %s %+.2f %s  txid=%s…", direction, count, tx.get("currency") or account.currency, txid[:16])
    return True


async def sync_wallet(session: AsyncSession, http: aiohttp.ClientSession, wallet: AccountWallet) -> int:
    """Sync one wallet. Returns the number of added transactions.

    First run (no records): sort=asc, per_page=50, walk all pages.
    Incremental (records exist): sort=desc, per_page=20 — stop
    when a page consists only of known txids.
    """
    seen = await known_txids(session, wallet.id)
    account = wallet.account
    network = wallet.network or NETWORK
    added = 0

    if not seen:
        # Full history load, ascending
        page = 1
        while True:
            items, pagination = await fetch_page(
                http, wallet.wallet_address, network, page=page, per_page=50, sort="asc"
            )
            if items is None:
                log.warning("  %s: address not found on the network", wallet.wallet_address)
                break
            if not items:
                break

            page_added = sum(_save_tx(session, wallet, account, tx, seen) for tx in items)
            added += page_added
            if page_added:
                await session.commit()

            total_pages = pagination.get("pages", 1)
            log.info("  [full] page %d/%d, added: %d", page, total_pages, page_added)
            if page >= total_pages:
                break
            page += 1
            await asyncio.sleep(0.3)
    else:
        # Incremental load: newest records first
        page = 1
        while True:
            items, pagination = await fetch_page(
                http, wallet.wallet_address, network, page=page, per_page=20, sort="desc"
            )
            if items is None:
                log.warning("  %s: address not found on the network", wallet.wallet_address)
                break
            if not items:
                break

            all_known = all(tx.get("txid", "") in seen for tx in items)
            page_added = sum(_save_tx(session, wallet, account, tx, seen) for tx in items)
            added += page_added
            if page_added:
                await session.commit()

            if all_known:
                log.info("  [incr] page %d — up to date, stopping", page)
                break
            log.info("  [incr] page %d/%d, added: %d", page, pagination.get("pages", 1), page_added)
            if page >= pagination.get("pages", 1):
                break
            page += 1
            await asyncio.sleep(0.3)

    return added


async def recalculate_wallet_balance(session: AsyncSession, wallet: AccountWallet) -> float:
    """Recalculate AccountWallet.balance as the sum of this wallet's transactions."""
    result = await session.execute(
        select(func.coalesce(func.sum(BlockchainHistory.count), 0.0))
        .where(BlockchainHistory.wallet_id == wallet.id)
    )
    balance = float(result.scalar())
    await session.execute(
        update(AccountWallet).where(AccountWallet.id == wallet.id).values(balance=balance)
    )
    return balance


async def recalculate_account_balance(session: AsyncSession, account_id) -> float:
    """Recalculate account.amount as the sum of all blockchain_history.count of the account."""
    result = await session.execute(
        select(func.coalesce(func.sum(BlockchainHistory.count), 0.0))
        .where(BlockchainHistory.account_id == account_id)
    )
    balance = float(result.scalar())
    await session.execute(
        update(Account).where(Account.id == account_id).values(amount=balance)
    )
    return balance


async def main():
    log.info("start  (api: %s, network: %s)", API_URL, NETWORK)
    engine = get_engine()
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            wallets = await get_all_wallets_with_accounts(session)
            log.info("wallets to sync: %d", len(wallets))

            # Group wallets by account to recalculate the balance after all of its wallets
            by_account: dict[any, list[AccountWallet]] = defaultdict(list)
            for w in wallets:
                by_account[w.account_id].append(w)

            async with aiohttp.ClientSession() as http:
                total_new = 0
                for account_id, account_wallets in by_account.items():
                    account = account_wallets[0].account
                    log.info("account %s (%s), wallets: %d",
                             account_id, account.currency, len(account_wallets))

                    added = 0
                    for wallet in account_wallets:
                        n = await sync_wallet(session, http, wallet)
                        wallet_balance = await recalculate_wallet_balance(session, wallet)
                        log.info("  wallet %s: balance %.2f (new: %d)",
                                 wallet.wallet_address, wallet_balance, n)
                        added += n
                        await asyncio.sleep(0.3)

                    await session.commit()
                    account_balance = await recalculate_account_balance(session, account_id)
                    await session.commit()
                    log.info("  account total: %+.2f (new transactions: %d)", account_balance, added)
                    total_new += added

            log.info("done, new transactions: %d", total_new)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
