import os
from aiohttp import web
from .handlers import (
    login_page, login_post, logout_handler, index_page,
    admin_api_groups, admin_api_accounts, admin_api_account_detail,
    admin_api_blockchain_history, admin_api_manual_history,
    admin_api_add_wallet, admin_api_delete_wallet, admin_api_update_wallet,
    admin_api_clear_blockchain_history, admin_api_update_amount,
)


def setup_admin(app: web.Application) -> None:
    p = os.getenv("ADMIN_PATH", "/admin").rstrip("/")
    app.router.add_get(f"{p}/login", login_page)
    app.router.add_post(f"{p}/login", login_post)
    app.router.add_post(f"{p}/logout", logout_handler)
    app.router.add_get(p or "/", index_page)
    app.router.add_get(f"{p}/", index_page)
    app.router.add_get(f"{p}/api/groups", admin_api_groups)
    app.router.add_get(f"{p}/api/accounts", admin_api_accounts)
    app.router.add_get(f"{p}/api/accounts/{{id}}", admin_api_account_detail)
    app.router.add_get(f"{p}/api/accounts/{{id}}/blockchain-history", admin_api_blockchain_history)
    app.router.add_delete(f"{p}/api/accounts/{{id}}/blockchain-history", admin_api_clear_blockchain_history)
    app.router.add_get(f"{p}/api/accounts/{{id}}/history", admin_api_manual_history)
    app.router.add_post(f"{p}/api/accounts/{{id}}/wallets", admin_api_add_wallet)
    app.router.add_delete(f"{p}/api/accounts/{{id}}/wallets/{{wallet_id}}", admin_api_delete_wallet)
    app.router.add_route("PATCH", f"{p}/api/accounts/{{id}}/wallets/{{wallet_id}}", admin_api_update_wallet)
    app.router.add_route("PATCH", f"{p}/api/accounts/{{id}}/amount", admin_api_update_amount)
