# Tally — team ledger in Telegram

[![CI](https://github.com/stefan-che/tally-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/stefan-che/tally-bot/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Optional companion to the **tron-cleanroom** stack (team bookkeeping and tracking wallets) → [overview](https://github.com/stefan-che/tron-cleanroom) · [architecture](https://github.com/stefan-che/tron-cleanroom/blob/main/ARCHITECTURE.md) · [full-stack quickstart](https://github.com/stefan-che/tron-cleanroom/blob/main/docs/QUICKSTART.md). Siblings: [cleanroom-watcher](https://github.com/stefan-che/cleanroom-watcher) · [cleanroom-vault](https://github.com/stefan-che/cleanroom-vault). It works on its own; the stack does not need it.

Add the bot to a Telegram group and the group gets its own **accounts** (one per currency or purpose). People post operations in the chat, the bot keeps the history and the balance. An account can also be bound to a crypto wallet, and then its balance follows the blockchain.

In the stack's crypto-hygiene story, Tally keeps the books for the clean wallets your funds are swept into: manual entries plus automatic balances from watched wallets.

**Status:** Production-proven: built and run in production as the processing stack of WOL, a Dubai OTC desk, 2022–2026. Stack: Python 3.11, aiogram 3, PostgreSQL 15, aiohttp.

**Scope:** automatic balances require the wallet address to be watched in [cleanroom-watcher](https://github.com/stefan-che/cleanroom-watcher).

## What you get

- **Accounts per Telegram group.** `/add usdt 2` creates an account with 2 decimals; `/usdt 1500 from client` adds, `/usdt -200*3 fee` subtracts (simple formulas).
- **Manual operations with undo.** Each operation is stored with author, comment and message link, and can be cancelled.
- **Automatic balances** for accounts bound to wallets: the sum of all transfers of the bound wallets, all currencies added together, refreshed every 5 minutes. The address must already be watched by [cleanroom-watcher](https://github.com/stefan-che/cleanroom-watcher); the bot does not register watches itself.
- **REST API** to list groups and accounts and to bind or unbind wallets: [docs/api.md](docs/api.md).
- **Statements.** History in chat and Excel export. Optional Google Sheets / Drive export (service-account JSON; share the sheet or folder with that account).
- **Backups.** `pg_dump` scripts, optional send to Telegram, optional public-key encrypted dump.
- **Rates.** `/rate ETH-BTC` reads Binance rates.

## Commands

| Command | What it does |
|---|---|
| `/start`, `/id`, `/help` | greeting and main keyboard, your user and chat ID, command help |
| `/add <name> [decimals]` | create an account |
| `/delete <name>` (`/del`) | delete an account |
| `/<name> <amount or formula> [comment]` | add to or subtract from an account, e.g. `/usdt -200*3 fee` |
| `/get [filter]` | list the chat's accounts |
| `/get_all [filters]` | all accounts of all groups, paged |
| `/history [name]` | transaction history |
| `/full_report` (`/excel`) | Excel statement |
| `/update_balance <name>` | recalculate a balance from its transactions |
| `/rate <coin1>[-<coin2>] [amount]` (`/cur`, `/currency`) | Binance rate, e.g. `/rate ETH-BTC` |
| `/me` (`/get_me`), `/users` (`/get_users`) | your role and groups; users of the group or system |
| `/add_user <id>` (`/create_user`), `/add_admin <id>` (`/create_admin`) | add a user or admin to the group (or the system in a private chat) |
| `/delete_user <id>`, `/update_role <id> <role>` (`/update_user_role`) | remove a user, change a system role |
| `/groups [search]` (`/get_groups`), `/group [id]` | list groups with filters; show one group |
| `/add_group [id]`, `/delete_group [id]`, `/change_group_type <id> <type>` | manage groups |
| `/migrate <old_chat_id>` | move a group's data after a supergroup upgrade |

Access depends on the system role and the group role (USER, ADMIN, SUPER_ADMIN). Commands without the slash also work for `add`, `delete`, `get`, `get_all`, `history`, `full_report`, `excel`, `update_balance` and `migrate`. The reply keyboard has **Full_report**, **Get**, **History** and **Help**.

## How automatic balances work

```
cleanroom-watcher (watches the address, stores its transfers)
     ▲  GET /api/addresses/{addr}/transactions, every 5 min
wallet_sync.py ─► blockchain history ─► account balance = Σ IN − Σ OUT
```

Bind a wallet in the web admin or with `POST /api/accounts/{id}/wallets`, then put the address on watch in cleanroom-watcher (`POST /api/watch`). If cleanroom-watcher answers 404 for an address, the wallet is skipped.

## Quick start

```bash
cp .env.sample .env     # set BOT_TOKEN, OWNER_ID, POSTGRES_PASSWORD, API_TOKEN, ADMIN_PASSWORD
docker compose up -d --build
docker compose --profile wallet-sync up -d    # optional: automatic balances
docker compose logs -f bot
```

Webhook mode, nginx, Google, backups and all variables: [docs/SETUP.md](docs/SETUP.md).

## Optional link with tron-cleanroom

tron-cleanroom can list ledger accounts and bind a recipient's destination wallets to them through this API (its "Ledger integration", off unless `LEDGER_API_URL` and `LEDGER_API_TOKEN` are set). Processing does not put those wallets on watch in cleanroom-watcher, so do that separately.

## Before you expose it

Set `API_TOKEN` (the API refuses requests without it), `ALLOWED_IPS`, `OWNER_ID`, a strong `ADMIN_PASSWORD`, and keep `USE_GUARD=true`. See [SECURITY.md](SECURITY.md).

## Docs

[docs/SETUP.md](docs/SETUP.md) · [docs/api.md](docs/api.md) · [SECURITY.md](SECURITY.md). Contributions and changelog: not set up yet.

## License

Licensed under the MIT License — see [LICENSE](LICENSE).
