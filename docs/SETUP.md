# Tally (tally-bot) — setup and operations

Overview: [../README.md](../README.md). API: [api.md](api.md). Security: [../SECURITY.md](../SECURITY.md).

## Run locally without Docker

```bash
cd bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.sample ../.env        # fill variables
python3 main.py
```

## Docker

```bash
docker compose up -d --build                  # postgres, alembic upgrade head, bot
docker compose --profile wallet-sync up -d    # optional: automatic balances every 5 min
docker compose logs -f bot
docker compose up -d --force-recreate bot     # after changing .env
```

Services: `pg` (Postgres 15, named volume, port bound to 127.0.0.1), `migrate` (one-shot), `bot` (Telegram + API + admin on `API_PORT`), `wallet-sync` (profile). To reach a cleanroom-watcher in another compose project, join its network (for example `processing-net`) as described in the comments of `docker-compose.yml`. Instead of the `wallet-sync` service you can run `wallet_sync.sh` from host cron.

## Configuration

All variables are in `.env.sample`.

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `BOT_TOKEN` | yes | | bot token from @BotFather |
| `OWNER_ID` | yes | | owner's Telegram user id; gets the start-up message |
| `USE_GUARD` | no | `true` in compose | only registered people and groups can use the bot |
| `DEBUG_PRINT_INPUT` | no | empty | `1` prints every incoming message (user, chat, text) to stdout; for local debugging only, keep it off in production |
| `WEBHOOK_HOST` | no | empty | public HTTPS address; if set, webhook mode is on |
| `WEBHOOK_PATH` | no | `/webhook/telegram` | use an unpredictable path |
| `WEBHOOK_SECRET` | no | empty | Telegram sends it in `X-Telegram-Bot-Api-Secret-Token`; the bot answers 403 on mismatch |
| `POSTGRES_HOST/PORT/USER/PASSWORD/DB` | password yes | `ledger` user and db | database; `POSTGRES_URL` is optional (Alembic) |
| `API_PORT` | no | `8080` | REST API, admin and webhook server |
| `API_TOKEN` | yes | | value of the `X-API-KEY` header |
| `ALLOWED_IPS` | no | empty | comma-separated IP allow-list for the API |
| `ADMIN_PATH`, `ADMIN_LOGIN`, `ADMIN_PASSWORD` | password yes | `/admin`, `admin` | web admin |
| `LISTENER_API_URL`, `LISTENER_API_KEY`, `LISTENER_NETWORK`, `WALLET_SYNC_INTERVAL` | no | `tron`, 300 s | cleanroom-watcher connection |
| `GOOGLE_CREDENTIAL_PATH`, `GOOGLE_SHARE_EMAIL`, `ROOT_FOLDER_NAME` | no | `Tally` (older deployments used `Ledger`; set it explicitly to keep an existing Drive folder) | Google export |
| `PG_CONTAINER_NAME`, `BACKUP_CHAT_ID` | no | `ledger-pg` | backup scripts |

## Webhook mode

Polling is the default and needs no public address. With `WEBHOOK_HOST` set, Telegram posts updates to your HTTPS URL.

```dotenv
WEBHOOK_HOST=https://ledger.example.com
WEBHOOK_PATH=/webhook/<long-random-string>
WEBHOOK_SECRET=<output of: python3 -c "import secrets; print(secrets.token_hex(32))">
```

```bash
python3 webhook.py set      # register (reads the variables above)
python3 webhook.py info     # URL, pending updates, whether a secret is set
python3 webhook.py delete   # back to polling on next start
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

### nginx and TLS

Telegram requires HTTPS. Get a certificate first, then enable SSL in nginx.

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d ledger.example.com           # DNS must point here, port 80 open
certbot renew --dry-run                          # renewal timer is installed by certbot
```

```nginx
server {
    listen 80;
    server_name ledger.example.com;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}
server {
    listen 443 ssl;
    server_name ledger.example.com;
    ssl_certificate     /etc/letsencrypt/live/ledger.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ledger.example.com/privkey.pem;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

`ALLOWED_IPS` reads the first address of `X-Forwarded-For`; add `proxy_set_header X-Forwarded-For $remote_addr;` so the proxy sets the real client address.

## Google Sheets / Drive export (optional)

Without `GOOGLE_CREDENTIAL_PATH` the bot runs normally and the export button says it is not configured.

1. Create a Google Cloud service account, enable the Drive and Sheets APIs, download its JSON key.
2. Mount it into the `bot` container (see the commented `volumes` in `docker-compose.yml`) and set `GOOGLE_CREDENTIAL_PATH` to the path inside the container.
3. Files are created on the service account's Drive under `ROOT_FOLDER_NAME`. Set `GOOGLE_SHARE_EMAIL` to get writer access, or share a sheet or folder with the service account's email.

## Backups

| Script | What it does |
|---|---|
| `backup.sh` / `db-restore.sh` | `pg_dump -Fc` to `./backup.dump`, optional send to Telegram (`BACKUP_CHAT_ID`) / restore |
| `backup-encrypt.sh` | SQL dump, bzip2, `openssl smime` with a public key, to `./backups/db_backup.sql.bz2.ssl` |
| `backup-decrypt.sh` / `backup-restore.sh` | decrypt with the private key (keep it off the server) / restore via `psql` |

Key generation is in the header of `backup-encrypt.sh`. Manual dump and restore:

```bash
docker exec ledger-pg pg_dump -U $POSTGRES_USER -Fc $POSTGRES_DB > ./backup.dump
docker exec -i ledger-pg pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists < ./backup.dump
```

Daily cron: `0 3 * * * cd /opt/tally-bot && ./backup.sh >> backup.log 2>&1`

## Migrations (Alembic)

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```
