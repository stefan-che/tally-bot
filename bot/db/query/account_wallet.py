import re
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..models.account_wallet import AccountWallet

_NETWORK_RE = re.compile(r"^[a-z0-9_-]{1,32}$")


def normalize_network(value) -> Optional[str]:
    """Normalize a wallet network name (tron, eth, ...). None if the value is invalid.

    Strict character allow-list: the value is rendered in the admin, including inside inline JS.
    """
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    return value if _NETWORK_RE.match(value) else None


async def add_account_wallet(
    session: AsyncSession, account_id: UUID, wallet_address: str, network: str = "tron"
) -> tuple[AccountWallet, bool]:
    """Add a wallet to an account. If it already exists, return the existing one (created=False)."""
    result = await session.execute(
        select(AccountWallet).where(
            AccountWallet.account_id == account_id,
            AccountWallet.wallet_address == wallet_address,
        )
    )
    existing = result.scalars().one_or_none()
    if existing:
        return existing, False

    wallet = AccountWallet(account_id=account_id, wallet_address=wallet_address, network=network)
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet, True


async def update_account_wallet_network(
    session: AsyncSession, wallet_id: UUID, network: str
) -> Optional[AccountWallet]:
    """Update the wallet network. Returns None if not found."""
    result = await session.execute(
        select(AccountWallet).where(AccountWallet.id == wallet_id)
    )
    wallet = result.scalars().one_or_none()
    if wallet is None:
        return None
    wallet.network = network
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def remove_account_wallet(session: AsyncSession, wallet_id: UUID) -> bool:
    """Delete a wallet by id. Returns False if not found."""
    result = await session.execute(
        select(AccountWallet).where(AccountWallet.id == wallet_id)
    )
    wallet = result.scalars().one_or_none()
    if wallet is None:
        return False
    await session.delete(wallet)
    await session.commit()
    return True


async def get_wallets_by_account(session: AsyncSession, account_id: UUID) -> list[AccountWallet]:
    result = await session.execute(
        select(AccountWallet).where(AccountWallet.account_id == account_id)
    )
    return list(result.scalars().all())


async def get_all_wallets_with_accounts(session: AsyncSession) -> list[AccountWallet]:
    """All wallets with their account data, for wallet_sync."""
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(AccountWallet).options(selectinload(AccountWallet.account))
    )
    return list(result.scalars().all())
