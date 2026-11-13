import os
import secrets
from uuid import UUID

from aiohttp import web
from sqlalchemy import select, func, or_, desc, cast, String, delete, update
from sqlalchemy.orm import selectinload

from db import session_maker
from db.models.account import Account
from db.models.account_wallet import AccountWallet
from db.models.blockchain_history import BlockchainHistory
from db.models.history import History
from db.models.group import Group
from db.query.account_wallet import add_account_wallet, remove_account_wallet, update_account_wallet_network, normalize_network
from db.query.account import get_account_by_id

# In-memory sessions {token: login} — reset when the bot restarts
_sessions: dict[str, str] = {}


def _admin_path() -> str:
    return os.getenv("ADMIN_PATH", "/admin").rstrip("/")


def _check_session(request: web.Request) -> bool:
    return request.cookies.get("admin_sid", "") in _sessions


def _require(request: web.Request):
    """Return a 401 response if the session is invalid, otherwise None."""
    if not _check_session(request):
        return web.json_response({"error": "Unauthorized"}, status=401)


# ── Login / Logout ────────────────────────────────────────────────────────────

def _login_html(error: str = "") -> str:
    err = f'<div class="alert alert-danger py-2 mb-3">{error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Admin · Sign in</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>body{{background:#f0f4ff;display:flex;align-items:center;justify-content:center;min-height:100vh}}</style>
</head>
<body>
  <div class="card shadow-sm" style="width:340px">
    <div class="card-body p-4">
      <h5 class="mb-4 text-center fw-bold">⚙ Admin Panel</h5>
      {err}
      <form method="post">
        <div class="mb-3">
          <input name="login" type="text" class="form-control" placeholder="Login" autofocus required>
        </div>
        <div class="mb-3">
          <input name="password" type="password" class="form-control" placeholder="Password" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">Sign in</button>
      </form>
    </div>
  </div>
</body>
</html>"""


async def login_page(request: web.Request) -> web.Response:
    if _check_session(request):
        raise web.HTTPFound(_admin_path() + "/")
    return web.Response(text=_login_html(), content_type="text/html")


async def login_post(request: web.Request) -> web.Response:
    data = await request.post()
    admin_login = os.getenv("ADMIN_LOGIN", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if not admin_password:
        return web.Response(
            text=_login_html("ADMIN_PASSWORD is not set in .env"), content_type="text/html"
        )
    if data.get("login") == admin_login and data.get("password") == admin_password:
        token = secrets.token_urlsafe(32)
        _sessions[token] = admin_login
        resp = web.HTTPFound(_admin_path() + "/")
        resp.set_cookie("admin_sid", token, httponly=True, samesite="Lax", max_age=86400 * 7)
        return resp

    return web.Response(text=_login_html("Invalid login or password"), content_type="text/html")


async def logout_handler(request: web.Request) -> web.Response:
    _sessions.pop(request.cookies.get("admin_sid", ""), None)
    resp = web.Response(text="ok")
    resp.del_cookie("admin_sid")
    return resp


async def index_page(request: web.Request) -> web.Response:
    if not _check_session(request):
        raise web.HTTPFound(_admin_path() + "/login")
    html = _ADMIN_HTML.replace("__ADMIN_PATH__", _admin_path())
    return web.Response(text=html, content_type="text/html")


# ── Admin API ─────────────────────────────────────────────────────────────────

async def admin_api_groups(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(50, max(1, int(request.rel_url.query.get("per_page", 20))))
    except ValueError:
        return web.json_response({"error": "invalid params"}, status=400)

    search = request.rel_url.query.get("search", "").strip()

    async with session_maker() as session:
        q = select(Group)
        cq = select(func.count()).select_from(Group)
        if search:
            pat = f"%{search}%"
            flt = or_(Group.title.ilike(pat), cast(Group.tg_id, String).ilike(pat))
            q = q.where(flt)
            cq = cq.where(flt)

        total = (await session.execute(cq)).scalar()
        groups = (
            await session.execute(q.order_by(desc(Group.tg_id)).offset((page - 1) * per_page).limit(per_page))
        ).scalars().all()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    return web.json_response({
        "data": [
            {
                "id": str(g.id),
                "tg_id": g.tg_id,
                "title": g.title,
                "status": str(g.status).split(".")[-1],
                "chat_type": str(g.chat_type).split(".")[-1],
            }
            for g in groups
        ],
        "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages},
    })


async def admin_api_accounts(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err

    group_id = request.rel_url.query.get("group_id")
    if not group_id:
        return web.json_response({"error": "group_id required"}, status=400)

    search = request.rel_url.query.get("search", "").strip()
    try:
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(50, max(1, int(request.rel_url.query.get("per_page", 20))))
    except ValueError:
        return web.json_response({"error": "invalid params"}, status=400)

    async with session_maker() as session:
        base_where = [Account.group_id == group_id]

        if search:
            pat = f"%{search}%"
            base_where.append(
                or_(Account.name.ilike(pat), cast(Account.user_id, String).ilike(pat))
            )

        total = (
            await session.execute(select(func.count()).select_from(Account).where(*base_where))
        ).scalar()

        accounts = (
            await session.execute(
                select(Account)
                .where(*base_where)
                .options(selectinload(Account.wallets))
                .order_by(desc(Account.amount))
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        ).scalars().all()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    return web.json_response({
        "data": [
            {
                "id": str(a.id),
                "name": a.name,
                "currency": a.currency,
                "amount": a.amount,
                "decimal": a.decimal,
                "wallets": [{"id": str(w.id), "wallet_address": w.wallet_address, "network": w.network, "balance": w.balance} for w in a.wallets],
            }
            for a in accounts
        ],
        "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages},
    })


async def admin_api_account_detail(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    async with session_maker() as session:
        account = await get_account_by_id(session, account_id)
        if not account:
            return web.json_response({"error": "not found"}, status=404)

    return web.json_response({
        "account": {
            "id": str(account.id),
            "group_id": str(account.group_id),
            "user_id": str(account.user_id),
            "name": account.name,
            "currency": account.currency,
            "amount": account.amount,
            "decimal": account.decimal,
        },
        "wallets": [{"id": str(w.id), "wallet_address": w.wallet_address, "network": w.network, "balance": w.balance} for w in account.wallets],
    })


def _hist_pagination(page, per_page, total):
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    return {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages}


async def admin_api_blockchain_history(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(100, max(1, int(request.rel_url.query.get("per_page", 50))))
    except ValueError:
        return web.json_response({"error": "invalid params"}, status=400)

    wallet = (request.rel_url.query.get("wallet") or "").strip()

    conditions = [BlockchainHistory.account_id == account_id]
    if wallet:
        conditions.append(BlockchainHistory.wallet_address.ilike(f"%{wallet}%"))

    async with session_maker() as session:
        total = (await session.execute(
            select(func.count()).select_from(BlockchainHistory)
            .where(*conditions)
        )).scalar()
        rows = (await session.execute(
            select(BlockchainHistory)
            .where(*conditions)
            .order_by(BlockchainHistory.time)
            .offset((page - 1) * per_page).limit(per_page)
        )).scalars().all()

    return web.json_response({
        "data": [
            {
                "txid": h.txid,
                "count": h.count,
                "currency": h.currency,
                "wallet_address": h.wallet_address,
                "time": h.time.isoformat() if h.time else None,
            }
            for h in rows
        ],
        "pagination": _hist_pagination(page, per_page, total),
    })


async def admin_api_manual_history(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(100, max(1, int(request.rel_url.query.get("per_page", 50))))
    except ValueError:
        return web.json_response({"error": "invalid params"}, status=400)

    async with session_maker() as session:
        total = (await session.execute(
            select(func.count()).select_from(History)
            .where(History.account_id == account_id)
        )).scalar()
        rows = (await session.execute(
            select(History)
            .where(History.account_id == account_id)
            .order_by(History.time)
            .offset((page - 1) * per_page).limit(per_page)
        )).scalars().all()

    return web.json_response({
        "data": [
            {
                "count": h.count,
                "currency": h.currency,
                "comment": h.comment,
                "username": h.username,
                "time": h.time.isoformat() if h.time else None,
                "is_cancelled": h.is_cancelled,
            }
            for h in rows
        ],
        "pagination": _hist_pagination(page, per_page, total),
    })


async def admin_api_add_wallet(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)

    addr = body.get("wallet_address", "")
    if not isinstance(addr, str) or not addr.strip():
        return web.json_response({"error": "wallet_address required"}, status=400)
    if len(addr) > 64:
        return web.json_response({"error": "wallet_address too long"}, status=400)

    network = normalize_network(body.get("network") or "tron")
    if network is None:
        return web.json_response({"error": "invalid network (allowed: a-z 0-9 _ -, max 32)"}, status=400)

    async with session_maker() as session:
        account = await get_account_by_id(session, account_id)
        if not account:
            return web.json_response({"error": "account not found"}, status=404)
        wallet, created = await add_account_wallet(session, account_id, addr.strip(), network)

    return web.json_response(
        {"id": str(wallet.id), "wallet_address": wallet.wallet_address, "network": wallet.network},
        status=201 if created else 200,
    )


async def admin_api_update_wallet(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        UUID(request.match_info["id"])
        wallet_id = UUID(request.match_info["wallet_id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)

    network = normalize_network(body.get("network", ""))
    if network is None:
        return web.json_response({"error": "invalid network (allowed: a-z 0-9 _ -, max 32)"}, status=400)

    async with session_maker() as session:
        wallet = await update_account_wallet_network(session, wallet_id, network)

    if wallet is None:
        return web.json_response({"error": "wallet not found"}, status=404)
    return web.json_response({"id": str(wallet.id), "network": wallet.network})


async def admin_api_delete_wallet(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        UUID(request.match_info["id"])
        wallet_id = UUID(request.match_info["wallet_id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    async with session_maker() as session:
        await session.execute(
            delete(BlockchainHistory).where(BlockchainHistory.wallet_id == wallet_id)
        )
        deleted = await remove_account_wallet(session, wallet_id)

    if not deleted:
        return web.json_response({"error": "wallet not found"}, status=404)
    return web.Response(status=204)


async def admin_api_clear_blockchain_history(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    async with session_maker() as session:
        result = await session.execute(
            delete(BlockchainHistory).where(BlockchainHistory.account_id == account_id)
        )
        await session.commit()

    return web.json_response({"deleted": result.rowcount})


async def admin_api_update_amount(request: web.Request) -> web.Response:
    if (err := _require(request)):
        return err
    try:
        account_id = UUID(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "invalid id"}, status=400)

    try:
        body = await request.json()
        amount = float(body["amount"])
    except (Exception, KeyError, TypeError, ValueError):
        return web.json_response({"error": "amount must be a number"}, status=400)

    async with session_maker() as session:
        account = await get_account_by_id(session, account_id)
        if not account:
            return web.json_response({"error": "not found"}, status=404)
        await session.execute(
            update(Account).where(Account.id == account_id).values(amount=amount)
        )
        await session.commit()

    return web.json_response({"amount": amount})


# ── HTML ──────────────────────────────────────────────────────────────────────

_ADMIN_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Admin Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    html, body { height: 100%; margin: 0; font-size: 14px; }
    .layout { display: flex; flex-direction: column; height: 100vh; }
    .topbar {
      background: #1a1a2e; color: #fff;
      padding: 10px 20px;
      display: flex; justify-content: space-between; align-items: center;
      flex-shrink: 0;
    }
    .panels { display: flex; flex: 1; overflow: hidden; background: #fff; }
    .panel { display: flex; flex-direction: column; border-right: 1px solid #dee2e6; overflow: hidden; }
    .panel-groups  { width: 230px; flex-shrink: 0; }
    .panel-accounts { width: 280px; flex-shrink: 0; }
    .panel-detail  { flex: 1; min-width: 0; }
    .panel-header {
      padding: 9px 14px; background: #f1f3f5;
      border-bottom: 1px solid #dee2e6;
      font-weight: 700; font-size: 11px; text-transform: uppercase;
      letter-spacing: .5px; color: #868e96; flex-shrink: 0;
    }
    .panel-body { overflow-y: auto; flex: 1; }
    .panel-footer { padding: 8px 12px; border-top: 1px solid #dee2e6; background: #f8f9fa; flex-shrink: 0; }
    .list-item { padding: 9px 14px; cursor: pointer; border-bottom: 1px solid #f1f1f1; }
    .list-item:hover { background: #f0f4ff; }
    .list-item.active { background: #e8efff; border-left: 3px solid #4361ee; padding-left: 11px; }
    .item-title { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .item-sub { font-size: 11px; color: #868e96; margin-top: 1px; }
    .badge-cur {
      font-size: 10px; padding: 2px 7px; border-radius: 10px;
      background: #e7ecff; color: #3451b2; font-weight: 700; flex-shrink: 0;
    }
    .detail-body { overflow-y: auto; flex: 1; }
    .section { padding: 16px 20px; border-bottom: 1px solid #f1f1f1; }
    .section-title { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #868e96; margin-bottom: 10px; }
    .wallet-chip {
      display: inline-flex; align-items: center; gap: 6px;
      background: #f0f4ff; border: 1px solid #c5d3f6;
      border-radius: 6px; padding: 4px 10px;
      font-size: 12px; font-family: monospace; margin: 3px;
    }
    .wallet-chip .rm { background: none; border: none; color: #dc3545; font-size: 14px; cursor: pointer; padding: 0; line-height: 1; }
    .net-badge {
      font-size: 10px; font-weight: 700; letter-spacing: .3px;
      background: #fff3bf; color: #a07e00; border-radius: 4px;
      padding: 1px 6px; font-family: inherit;
    }
    .bch-filter {
      display: flex; align-items: center; gap: 10px;
      background: #f8faff; border: 1px solid #dce4f5; border-radius: 8px;
      padding: 8px 12px; margin-bottom: 12px;
    }
    .bch-filter-label { font-size: 12px; font-weight: 600; color: #3451b2; white-space: nowrap; }
    .bch-filter input { max-width: 340px; font-family: monospace; font-size: 12px; }
    .history-table { font-size: 12px; }
    .history-table th, .history-table td { padding: 5px 8px; }
    .tx-in  { color: #2f9e44; font-weight: 600; }
    .tx-out { color: #e03131; font-weight: 600; }
    .mono { font-family: monospace; font-size: 11px; color: #868e96; }
    .empty { text-align: center; color: #ced4da; padding: 40px 20px; font-size: 13px; }
    .page-info { font-size: 12px; color: #868e96; }
    .balance { font-size: 26px; font-weight: 700; color: #1c7ed6; letter-spacing: -.5px; }
  </style>
</head>
<body>
<div class="layout">

  <div class="topbar">
    <span style="font-weight:700;font-size:15px">⚙ Admin Panel</span>
    <button class="btn btn-sm btn-outline-light" onclick="doLogout()">Sign out</button>
  </div>

  <div class="panels">

    <!-- Groups -->
    <div class="panel panel-groups">
      <div class="panel-header">Groups</div>
      <div class="panel-body" id="groups-body"></div>
      <div class="panel-footer">
        <input id="g-search" type="search" class="form-control form-control-sm mb-2"
               placeholder="Title or tg_id…" oninput="onGroupSearch(this.value)">
        <div class="d-flex justify-content-between align-items-center">
          <button class="btn btn-sm btn-outline-secondary" id="g-prev" onclick="gPage(-1)">‹</button>
          <span class="page-info" id="g-info">—</span>
          <button class="btn btn-sm btn-outline-secondary" id="g-next" onclick="gPage(1)">›</button>
        </div>
      </div>
    </div>

    <!-- Accounts -->
    <div class="panel panel-accounts">
      <div class="panel-header">Accounts</div>
      <div class="panel-body" id="accounts-body">
        <div class="empty">Select a group</div>
      </div>
      <div class="panel-footer">
        <input id="search" type="search" class="form-control form-control-sm mb-2"
               placeholder="Name or user_id…" oninput="onSearch(this.value)">
        <div class="d-flex justify-content-between align-items-center">
          <button class="btn btn-sm btn-outline-secondary" id="a-prev" onclick="aPage(-1)">‹</button>
          <span class="page-info" id="a-info">—</span>
          <button class="btn btn-sm btn-outline-secondary" id="a-next" onclick="aPage(1)">›</button>
        </div>
      </div>
    </div>

    <!-- Detail -->
    <div class="panel panel-detail">
      <div class="panel-header">Account details</div>
      <div class="detail-body" id="detail-body">
        <div class="empty">Select an account</div>
      </div>
    </div>

  </div>
</div>

<script>
const ADMIN_PATH = '__ADMIN_PATH__';
const S = {
  groupId: null, accountId: null,
  gPage: 1, gTotal: 1, gSearch: '', gSearchTimer: null,
  aPage: 1, aTotal: 0, search: '', searchTimer: null,
  histTab: 'blockchain',
  bchPage: 1, bchTotal: 0, bchWallet: '', bchWalletTimer: null,
  manPage: 1, manTotal: 0,
  currentDecimal: 2,
};

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function fmt(n, d = 2) {
  return Number(n).toLocaleString('en-US', {minimumFractionDigits:d, maximumFractionDigits:d});
}
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
  return d.toLocaleDateString('en-US', {day:'2-digit',month:'2-digit',year:'2-digit'})
       + ' ' + d.toLocaleTimeString('en-US', {hour:'2-digit',minute:'2-digit'});
}

async function req(path, opts = {}) {
  let r;
  try {
    r = await fetch(ADMIN_PATH + '/api' + path, {
      headers: {'Content-Type': 'application/json', ...opts.headers},
      ...opts,
    });
  } catch (e) { console.error(e); return null; }
  if (r.status === 401) { location.href = ADMIN_PATH + '/login'; return null; }
  if (r.status === 204) return {};
  const body = await r.json().catch(() => ({}));
  if (!r.ok) { alert('Error: ' + (body.error || r.status)); return null; }
  return body;
}

// ── Groups ────────────────────────────────────────────────────────────────────

async function loadGroups() {
  const q = new URLSearchParams({page: S.gPage, per_page: 20});
  if (S.gSearch) q.set('search', S.gSearch);
  const data = await req(`/groups?${q}`);
  if (!data) return;
  S.gTotal = Math.max(1, data.pagination.total_pages);
  document.getElementById('g-info').textContent = `${S.gPage} / ${S.gTotal}`;
  document.getElementById('g-prev').disabled = S.gPage <= 1;
  document.getElementById('g-next').disabled = S.gPage >= S.gTotal;

  const el = document.getElementById('groups-body');
  if (!data.data.length) { el.innerHTML = '<div class="empty">No groups</div>'; return; }
  el.innerHTML = data.data.map(g => `
    <div class="list-item ${g.id === S.groupId ? 'active' : ''}" onclick="selectGroup('${g.id}')">
      <div class="item-title">${esc(g.title || '—')}</div>
      <div class="item-sub">${esc(g.chat_type)} · ${esc(g.status)}</div>
    </div>
  `).join('');
}

function gPage(d) {
  const n = S.gPage + d;
  if (n < 1 || n > S.gTotal) return;
  S.gPage = n; loadGroups();
}

function onGroupSearch(val) {
  clearTimeout(S.gSearchTimer);
  S.gSearchTimer = setTimeout(() => { S.gSearch = val.trim(); S.gPage = 1; loadGroups(); }, 300);
}

function selectGroup(id) {
  S.groupId = id; S.accountId = null;
  S.aPage = 1; S.search = '';
  document.getElementById('search').value = '';
  document.getElementById('detail-body').innerHTML = '<div class="empty">Select an account</div>';
  loadGroups();
  loadAccounts();
}

// ── Accounts ──────────────────────────────────────────────────────────────────

async function loadAccounts() {
  if (!S.groupId) return;
  const q = new URLSearchParams({group_id: S.groupId, page: S.aPage, per_page: 20});
  if (S.search) q.set('search', S.search);
  const data = await req(`/accounts?${q}`);
  if (!data) return;
  S.aTotal = data.pagination.total_pages;
  const tp = Math.max(1, S.aTotal);
  document.getElementById('a-info').textContent = `${S.aPage} / ${tp}`;
  document.getElementById('a-prev').disabled = S.aPage <= 1;
  document.getElementById('a-next').disabled = S.aPage >= S.aTotal;

  const el = document.getElementById('accounts-body');
  if (!data.data.length) { el.innerHTML = '<div class="empty">No accounts</div>'; return; }
  el.innerHTML = data.data.map(a => `
    <div class="list-item ${a.id === S.accountId ? 'active' : ''}" onclick="selectAccount('${a.id}')">
      <div class="item-title d-flex justify-content-between align-items-center gap-1">
        <span>${esc(a.name)}</span>
        <span class="badge-cur">${esc(a.currency.toUpperCase())}</span>
      </div>
      <div class="item-sub">${fmt(a.amount, a.decimal)} · ${a.wallets.length} wallets</div>
    </div>
  `).join('');
}

function aPage(d) {
  const n = S.aPage + d;
  if (n < 1 || n > S.aTotal) return;
  S.aPage = n; loadAccounts();
}

function onSearch(val) {
  clearTimeout(S.searchTimer);
  S.searchTimer = setTimeout(() => { S.search = val.trim(); S.aPage = 1; loadAccounts(); }, 300);
}

// ── Account detail ─────────────────────────────────────────────────────────────

async function selectAccount(id, pushHash = true) {
  S.accountId = id;
  S.histTab = 'manual'; S.bchPage = 1; S.manPage = 1; S.currentDecimal = 2; S.bchWallet = '';
  if (pushHash) history.replaceState(null, '', '#account=' + id);
  loadAccounts();
  const data = await req(`/accounts/${id}`);
  if (!data) return;

  const a = data.account;
  const dec = a.decimal;
  S.currentDecimal = dec;

  const hasWallets = data.wallets.length > 0;

  const walletsHtml = hasWallets
    ? data.wallets.map(w => `
        <span class="wallet-chip" id="wchip-${w.id}">
          <span>${esc(w.wallet_address)}</span>
          <span class="net-badge" title="Network">${esc((w.network || 'tron').toUpperCase())}</span>
          <button class="rm" style="color:#1c7ed6" onclick="editWalletNetwork('${a.id}','${w.id}','${esc(w.network || 'tron')}')" title="Change network">✎</button>
          <span style="color:#2f9e44;font-weight:600;font-size:12px">${fmt(w.balance, dec)}</span>
          <button class="rm" onclick="removeWallet('${a.id}','${w.id}')" title="Remove">✕</button>
        </span>`).join('')
    : '<span style="color:#adb5bd;font-size:13px">No wallets</span>';

  document.getElementById('detail-body').innerHTML = `
    <div class="section">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <div style="font-size:17px;font-weight:700">${esc(a.name)}</div>
          <div class="mono" style="color:#adb5bd;font-size:11px;margin-top:2px">ID: ${esc(a.id)}</div>
          <div class="mono" style="color:#adb5bd;font-size:11px;margin-top:2px">Group id: ${esc(a.group_id)}</div>
          <div class="mono" style="color:#adb5bd;font-size:11px;margin-top:2px">User id: ${esc(a.user_id)}</div>
        </div>
        <span class="badge-cur" style="font-size:13px">${esc(a.currency.toUpperCase())}</span>
      </div>
      <div class="d-flex align-items-center gap-2 mt-2">
        <div class="balance" id="balance-display">${fmt(a.amount, dec)}</div>
        ${hasWallets ? `<button class="btn btn-outline-secondary" style="padding:2px 8px;font-size:12px;line-height:1.4"
                onclick="editAmount('${a.id}', ${a.amount})" title="Edit amount">✎</button>` : ''}
      </div>
    </div>

    <div class="section">
      <div class="section-title">Wallets</div>
      <div id="wallets-wrap">${walletsHtml}</div>
      <div class="d-flex gap-2 mt-3">
        <input id="wallet-input" type="text" class="form-control form-control-sm"
               placeholder="TRx…" style="max-width:320px;font-family:monospace;font-size:12px"
               onkeydown="if(event.key==='Enter') addWallet('${a.id}')">
        <input id="wallet-network" type="text" class="form-control form-control-sm"
               placeholder="tron" value="tron" style="max-width:110px;font-size:12px"
               onkeydown="if(event.key==='Enter') addWallet('${a.id}')">
        <button class="btn btn-sm btn-primary" onclick="addWallet('${a.id}')">+ Add</button>
      </div>
    </div>

    <div class="section" style="border-bottom:none;padding-bottom:32px">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <ul class="nav nav-tabs mb-0 border-0" style="font-size:12px">
          <li class="nav-item">
            <button class="nav-link active" id="tab-man" onclick="switchTab('manual')">✏ Manual operations</button>
          </li>
          ${hasWallets ? `<li class="nav-item">
            <button class="nav-link" id="tab-bc" onclick="switchTab('blockchain')">🔗 Blockchain</button>
          </li>` : ''}
        </ul>
        <div id="hist-actions"></div>
      </div>
      <div id="hist-content"><div class="empty">Loading…</div></div>
      <div class="d-flex justify-content-between align-items-center mt-2" id="hist-pager"></div>
    </div>
  `;
  loadHistory();
}

function switchTab(tab) {
  S.histTab = tab;
  const bcBtn = document.getElementById('tab-bc');
  if (bcBtn) bcBtn.classList.toggle('active', tab === 'blockchain');
  document.getElementById('tab-man').classList.toggle('active', tab === 'manual');
  if (tab === 'blockchain') S.bchPage = 1; else S.manPage = 1;
  loadHistory();
}

function loadHistory() {
  if (S.histTab === 'blockchain') loadBlockchainHistory();
  else loadManualHistory();
}

async function loadBlockchainHistory() {
  const q = S.bchWallet ? `&wallet=${encodeURIComponent(S.bchWallet)}` : '';
  const data = await req(`/accounts/${S.accountId}/blockchain-history?page=${S.bchPage}&per_page=50${q}`);
  if (!data) return;
  S.bchTotal = data.pagination.total_pages;
  const dec = S.currentDecimal;

  ensureBchFilter();

  const actEl = document.getElementById('hist-actions');
  if (actEl) {
    const total = data.pagination.total;
    actEl.innerHTML = `<span class="text-muted me-2" style="font-size:12px">Total: ${total}</span>`
      + (total > 0 ? `<button class="btn btn-sm btn-outline-danger" onclick="clearBlockchainHistory('${S.accountId}')">🗑 Clear transactions</button>` : '');
  }

  const html = data.data.length
    ? `<table class="table table-sm table-hover history-table mb-0">
        <thead class="table-light"><tr>
          <th>Date</th><th>Amount</th><th>Currency</th><th>Wallet</th><th>txid</th>
        </tr></thead>
        <tbody>${data.data.map(h => `
          <tr>
            <td>${fmtDate(h.time)}</td>
            <td class="${h.count > 0 ? 'tx-in' : 'tx-out'}">${h.count > 0 ? '+' : ''}${fmt(h.count, dec)}</td>
            <td>${esc(h.currency)}</td>
            <td class="mono" title="${h.wallet_address ? esc(h.wallet_address) : ''}">${h.wallet_address ? esc(h.wallet_address.slice(0,8)) + '…' + esc(h.wallet_address.slice(-6)) : '—'}</td>
            <td class="mono" title="${esc(h.txid)}">${esc(h.txid.slice(0,16))}…</td>
          </tr>`).join('')}
        </tbody>
      </table>`
    : '<div class="empty" style="padding:20px">No transactions</div>';

  document.getElementById('hist-content').innerHTML = html;
  renderHistPager(S.bchPage, S.bchTotal);
}

function filterBlockchain(val) {
  S.bchWallet = val;
  clearTimeout(S.bchWalletTimer);
  S.bchWalletTimer = setTimeout(() => { S.bchPage = 1; loadBlockchainHistory(); }, 300);
}

function ensureBchFilter() {
  if (document.getElementById('bch-filter-bar')) return;
  const content = document.getElementById('hist-content');
  if (!content) return;
  const bar = document.createElement('div');
  bar.id = 'bch-filter-bar';
  bar.className = 'bch-filter';
  bar.innerHTML = `
    <span class="bch-filter-label">🔍 Filter by wallet</span>
    <input id="bch-wallet-filter" type="text" class="form-control form-control-sm"
           placeholder="paste an address or part of it" value="${esc(S.bchWallet)}"
           oninput="filterBlockchain(this.value)">
    <button class="btn btn-sm btn-outline-secondary" type="button" onclick="clearBchFilter()" title="Clear filter">✕</button>`;
  content.parentElement.insertBefore(bar, content);
}

function removeBchFilter() {
  const bar = document.getElementById('bch-filter-bar');
  if (bar) bar.remove();
}

function clearBchFilter() {
  S.bchWallet = '';
  const inp = document.getElementById('bch-wallet-filter');
  if (inp) inp.value = '';
  S.bchPage = 1;
  loadBlockchainHistory();
}

async function loadManualHistory() {
  removeBchFilter();
  const actEl = document.getElementById('hist-actions');
  if (actEl) actEl.innerHTML = '';
  const data = await req(`/accounts/${S.accountId}/history?page=${S.manPage}&per_page=50`);
  if (!data) return;
  S.manTotal = data.pagination.total_pages;
  const dec = S.currentDecimal;

  const html = data.data.length
    ? `<table class="table table-sm table-hover history-table mb-0">
        <thead class="table-light"><tr>
          <th>Date</th><th>Amount</th><th>Currency</th><th>Comment</th><th>User</th><th>Cancelled</th>
        </tr></thead>
        <tbody>${data.data.map(h => `
          <tr class="${h.is_cancelled ? 'text-decoration-line-through text-muted' : ''}">
            <td>${fmtDate(h.time)}</td>
            <td class="${h.count > 0 ? 'tx-in' : 'tx-out'}">${h.count > 0 ? '+' : ''}${fmt(h.count, dec)}</td>
            <td>${esc(h.currency)}</td>
            <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(h.comment)}</td>
            <td class="mono">${esc(h.username || '—')}</td>
            <td>${h.is_cancelled ? '✓' : ''}</td>
          </tr>`).join('')}
        </tbody>
      </table>`
    : '<div class="empty" style="padding:20px">No operations</div>';

  document.getElementById('hist-content').innerHTML = html;
  renderHistPager(S.manPage, S.manTotal);
}

function renderHistPager(page, total) {
  const tp = Math.max(1, total);
  document.getElementById('hist-pager').innerHTML = total > 1 ? `
    <button class="btn btn-sm btn-outline-secondary" onclick="histPage(-1)" ${page <= 1 ? 'disabled' : ''}>‹</button>
    <span class="page-info">${page} / ${tp}</span>
    <button class="btn btn-sm btn-outline-secondary" onclick="histPage(1)" ${page >= total ? 'disabled' : ''}>›</button>
  ` : '';
}

function histPage(d) {
  if (S.histTab === 'blockchain') {
    const n = S.bchPage + d;
    if (n < 1 || n > S.bchTotal) return;
    S.bchPage = n; loadBlockchainHistory();
  } else {
    const n = S.manPage + d;
    if (n < 1 || n > S.manTotal) return;
    S.manPage = n; loadManualHistory();
  }
}


async function addWallet(accountId) {
  const inp = document.getElementById('wallet-input');
  const netInp = document.getElementById('wallet-network');
  const addr = inp.value.trim();
  const network = (netInp.value.trim() || 'tron');
  if (!addr) return;
  const r = await req(`/accounts/${accountId}/wallets`, {
    method: 'POST',
    body: JSON.stringify({wallet_address: addr, network}),
  });
  if (r !== null) { inp.value = ''; netInp.value = 'tron'; selectAccount(accountId); loadAccounts(); }
}

async function removeWallet(accountId, walletId) {
  if (!confirm('Remove this wallet?')) return;
  const r = await req(`/accounts/${accountId}/wallets/${walletId}`, {method: 'DELETE'});
  if (r !== null) { selectAccount(accountId); loadAccounts(); }
}

function editWalletNetwork(accountId, walletId, current) {
  const network = prompt('Wallet network:', current || 'tron');
  if (network === null) return;
  saveWalletNetwork(accountId, walletId, network.trim());
}

async function saveWalletNetwork(accountId, walletId, network) {
  if (!network) { alert('Network cannot be empty'); return; }
  const r = await req(`/accounts/${accountId}/wallets/${walletId}`, {
    method: 'PATCH',
    body: JSON.stringify({network}),
  });
  if (r !== null) { selectAccount(accountId); loadAccounts(); }
}

async function doLogout() {
  await fetch(ADMIN_PATH + '/logout', {method: 'POST'});
  location.href = ADMIN_PATH + '/login';
}

// Amount editing

function editAmount(accountId, current) {
  const balanceEl = document.getElementById('balance-display');
  if (!balanceEl) return;
  const wrap = balanceEl.parentElement;
  wrap.innerHTML = `
    <input id="amount-inp" type="number" step="any" class="form-control form-control-sm"
           style="max-width:160px;font-size:18px;font-weight:700" value="${current}"
           onkeydown="if(event.key==='Enter'){event.preventDefault();saveAmount('${accountId}');}
                      if(event.key==='Escape') selectAccount('${accountId}', false);">
    <button class="btn btn-sm btn-primary" onclick="saveAmount('${accountId}')">Save</button>
    <button class="btn btn-sm btn-outline-secondary" onclick="selectAccount('${accountId}', false)">Cancel</button>
  `;
  const inp = document.getElementById('amount-inp');
  if (inp) { inp.focus(); inp.select(); }
}

async function saveAmount(accountId) {
  const inp = document.getElementById('amount-inp');
  if (!inp) return;
  const val = parseFloat(inp.value);
  if (isNaN(val)) { alert('Enter a valid number'); return; }
  const r = await req(`/accounts/${accountId}/amount`, {
    method: 'PATCH',
    body: JSON.stringify({amount: val}),
  });
  if (r !== null) { await selectAccount(accountId, false); loadAccounts(); }
}

async function clearBlockchainHistory(accountId) {
  if (!confirm('Delete all blockchain transactions of this account? This cannot be undone.')) return;
  const r = await req(`/accounts/${accountId}/blockchain-history`, {method: 'DELETE'});
  if (r !== null) {
    S.bchPage = 1;
    loadBlockchainHistory();
  }
}

// ── Deep link: restore state from the URL hash ────────────────────────────────────

async function restoreFromHash(accountId) {
  const detail = await req(`/accounts/${accountId}`);
  if (!detail) { loadGroups(); return; }

  S.groupId = detail.account.group_id;
  S.accountId = accountId;

  // Load groups and accounts in parallel, then render the details
  await Promise.all([loadGroups(), loadAccounts()]);
  await selectAccount(accountId, false);
}

function getHashAccount() {
  const p = new URLSearchParams(window.location.hash.slice(1));
  return p.get('account');
}

window.addEventListener('hashchange', () => {
  const id = getHashAccount();
  if (id && id !== S.accountId) restoreFromHash(id);
});

// Start: open from the hash or just load the groups
const _initAccount = getHashAccount();
if (_initAccount) restoreFromHash(_initAccount);
else loadGroups();
</script>
</body>
</html>"""
