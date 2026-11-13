import traceback
from uuid import UUID
from aiohttp import web
from db import session_maker
from db.query.account import get_accounts_paginated, get_account_by_id
from db.query.account_wallet import add_account_wallet, remove_account_wallet, normalize_network


def _account_dict(a) -> dict:
    return {
        "id": str(a.id),
        "group_id": str(a.group_id),
        "user_id": a.user_id,
        "name": a.name,
        "currency": a.currency,
        "amount": a.amount,
        "decimal": a.decimal,
        "wallets": [{"id": str(w.id), "wallet_address": w.wallet_address, "network": w.network, "balance": w.balance} for w in a.wallets],
    }


async def get_accounts(request: web.Request) -> web.Response:
    try:
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(100, max(1, int(request.rel_url.query.get("per_page", 20))))
    except ValueError:
        return web.json_response({"error": "page and per_page must be integers"}, status=400)

    raw_user_id = request.rel_url.query.get("user_id")
    raw_group_id = request.rel_url.query.get("group_id")

    try:
        user_id = int(raw_user_id) if raw_user_id is not None else None
    except ValueError:
        return web.json_response({"error": "user_id must be an integer"}, status=400)

    group_id = raw_group_id  # UUID string — Account.group_id is a UUID foreign key

    try:
        async with session_maker() as session:
            accounts, total = await get_accounts_paginated(
                session, page=page, per_page=per_page, user_id=user_id, group_id=group_id
            )
    except Exception as e:
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return web.json_response({
        "data": [_account_dict(a) for a in accounts],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    })


async def post_account_wallet(request: web.Request) -> web.Response:
    try:
        account_id = UUID(request.match_info["id"])
    except (ValueError, KeyError):
        return web.json_response({"error": "invalid account id"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)

    if "wallet_address" not in body:
        return web.json_response({"error": "wallet_address field is required"}, status=400)

    wallet_address = body["wallet_address"]
    if not isinstance(wallet_address, str):
        return web.json_response({"error": "wallet_address must be a string"}, status=400)
    if len(wallet_address) > 64:
        return web.json_response({"error": "wallet_address must not exceed 64 characters"}, status=400)

    network = normalize_network(body.get("network") or "tron")
    if network is None:
        return web.json_response({"error": "network must match ^[a-z0-9_-]{1,32}$"}, status=400)

    try:
        async with session_maker() as session:
            account = await get_account_by_id(session, account_id)
            if account is None:
                return web.json_response({"error": "account not found"}, status=404)
            wallet, created = await add_account_wallet(session, account_id, wallet_address, network)
    except Exception as e:
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

    return web.json_response(
        {"id": str(wallet.id), "account_id": str(wallet.account_id),
         "wallet_address": wallet.wallet_address, "network": wallet.network},
        status=201 if created else 200,
    )


async def delete_account_wallet(request: web.Request) -> web.Response:
    try:
        UUID(request.match_info["id"])
        wallet_id = UUID(request.match_info["wallet_id"])
    except (ValueError, KeyError):
        return web.json_response({"error": "invalid id"}, status=400)

    try:
        async with session_maker() as session:
            deleted = await remove_account_wallet(session, wallet_id)
    except Exception as e:
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

    if not deleted:
        return web.json_response({"error": "wallet not found"}, status=404)

    return web.Response(status=204)
