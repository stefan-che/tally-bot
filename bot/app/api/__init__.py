import os
import traceback
from aiohttp import web
from .groups import get_groups
from .accounts import get_accounts, post_account_wallet, delete_account_wallet
from ..admin import setup_admin

_UNPROTECTED = {"/health"}

def _get_allowed_ips() -> set[str]:
    raw = os.getenv("ALLOWED_IPS", "")
    return {ip.strip() for ip in raw.split(",") if ip.strip()}


@web.middleware
async def auth_middleware(request: web.Request, handler):
    admin_prefix = os.getenv("ADMIN_PATH", "/admin").rstrip("/")
    if request.path in _UNPROTECTED or request.path.startswith(admin_prefix):
        return await handler(request)

    allowed_ips = _get_allowed_ips()
    if allowed_ips:
        client_ip = request.headers.get("X-Forwarded-For", request.remote or "").split(",")[0].strip()
        if client_ip not in allowed_ips:
            return web.json_response({"error": "Forbidden"}, status=403)

    api_token = os.getenv("API_TOKEN", "")
    if not api_token:
        return web.json_response({"error": "API_TOKEN is not configured on server"}, status=500)

    if request.headers.get("X-API-KEY", "") != api_token:
        return web.json_response({"error": "Unauthorized"}, status=401)

    return await handler(request)


@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app(dp=None) -> web.Application:
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook/telegram")

    if dp is not None:
        # Reserve the webhook path so auth_middleware lets it through; the
        # aiogram 3 SimpleRequestHandler registers the actual route in main.py.
        _UNPROTECTED.add(webhook_path)

    app = web.Application(middlewares=[error_middleware, auth_middleware])
    app.router.add_get("/health", health)
    app.router.add_get("/api/groups", get_groups)
    app.router.add_get("/api/accounts", get_accounts)
    app.router.add_post("/api/accounts/{id}/wallets", post_account_wallet)
    app.router.add_delete("/api/accounts/{id}/wallets/{wallet_id}", delete_account_wallet)
    setup_admin(app)

    return app