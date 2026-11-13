# CLAUDE.md — tally-bot

Guide for developers and AI agents. Product overview: [README.md](README.md).

## What this is
Tally, a Telegram bookkeeping bot (Python 3.11, aiogram 3, PostgreSQL 15, SQLAlchemy async + Alembic, aiohttp).
Every Telegram group has accounts; balances change by chat operations (manual accounts, table
`history`) or follow bound wallets (automatic accounts, tables `account_wallets` +
`blockchain_history`). Part of the stack next to it: `../cleanroom-watcher` supplies transfers,
`../tron-cleanroom` can bind wallets through the HTTP API.

## Commands
```bash
docker compose up -d --build                       # pg → migrate (alembic upgrade head) → bot
docker compose --profile wallet-sync up -d         # + wallet_sync.py loop (WALLET_SYNC_INTERVAL)
cd bot && alembic revision --autogenerate -m "..."  # new migration (needs POSTGRES_* env)
cd bot && python -m pytest tests                   # unit tests (pure functions, no DB)
docker run --rm -v "$PWD":/app -w /app python:3.11-slim python -m compileall -q bot   # syntax check
```
Run locally: `cd bot && pip install -r requirements.txt && python3 main.py` with `.env` in `bot/` or
the environment set (see `.env.sample`).

## Code map
| Path | Role |
|---|---|
| `bot/main.py` | wiring: Bot + Dispatcher, middlewares, commands/handlers/scenes, aiohttp app, polling or webhook |
| `bot/src/commands/` | chat commands; `router/` dispatches by chat type to `user/` and `admin/` |
| `bot/src/handlers/` | callback handlers: pages, sorting, cancel, reports (`reports/` Excel and Google) |
| `bot/src/FCM/` | FSM scenes (add operation flow) |
| `bot/src/middlewares/` | guard (`USE_GUARD`), router, click throttling, input logging |
| `bot/src/utils/` | layout, paging, access (`OWNER_ID` → owner role), group links/migration |
| `bot/app/api/` | HTTP API (`X-API-KEY` = `API_TOKEN`, `ALLOWED_IPS`) — see `docs/api.md` |
| `bot/app/admin/` | web admin (login/password from env, inline HTML) |
| `bot/app/google/` | optional Drive/Sheets export; `google_enabled()` gates it |
| `bot/app/xlsx/`, `bot/app/exchanges/` | Excel export; Binance/XE rates |
| `bot/db/` | `models/`, `query/`, `engine.py`, `migration/` (Alembic, `alembic.ini` in `bot/`) |
| `bot/wallet_sync.py` | cleanroom-watcher `GET /api/addresses/{addr}/transactions` → `blockchain_history` → `account.amount` |
| `*.sh` (root) | backups/restore, host-cron wrapper for wallet sync |

## Conventions
- Configuration only through environment variables (`os.getenv`), documented in `.env.sample`.
  Add a new variable there and in `docker-compose.yml` (`x-bot-env`).
- Schema changes only through Alembic migrations in `bot/db/migration/versions/`.
- Bot texts, commands and the web admin are English; keep new user-facing texts in English.
- Optional integrations (Google, cleanroom-watcher) must not block start-up: guard them and answer
  "not configured" at use time.
- The bot never registers cleanroom-watcher watches; that is cleanroom-watcher's API / admin.
- No real ids, emails or hosts in code, tests or docs; use placeholders (`example.com`, `0`).
