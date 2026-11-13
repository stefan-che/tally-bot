# Security

## Reporting

Report a security issue privately via [GitHub security advisories](https://github.com/stefan-che/tron-cleanroom/security/advisories/new), not in a public issue. Use the single channel described in the tron-cleanroom repo: [tron-cleanroom/SECURITY.md](https://github.com/stefan-che/tron-cleanroom/blob/main/SECURITY.md).

## Built-in protection

- **API token.** Every endpoint except `/health` requires the `X-API-KEY` header equal to `API_TOKEN`; with no token configured the API serves nothing.
- **IP allow-list.** Set `ALLOWED_IPS` and only those addresses are served.
- **Owner-only commands.** `OWNER_ID` is the owner; with `USE_GUARD=true` only registered people and groups can use the bot.
- **Web admin login.** The admin lives at `ADMIN_PATH` behind `ADMIN_LOGIN` / `ADMIN_PASSWORD`.
- **Webhook mode.** `WEBHOOK_SECRET` and a custom `WEBHOOK_PATH` are supported.
- **Encrypted backups.** `backup-encrypt.sh` encrypts dumps with a public key, so the private key can stay off the server.

## Production hardening checklist

- Set `API_TOKEN` and `ALLOWED_IPS`.
- Run behind a reverse proxy that sets the client IP header (`X-Forwarded-For`); do not expose the app port directly.
- Use a strong `ADMIN_PASSWORD` and restrict `ADMIN_PATH` at the proxy.
- Keep `USE_GUARD=true`; set `WEBHOOK_SECRET` and an unpredictable `WEBHOOK_PATH` in webhook mode.
- Keep secrets (`.env`, Google JSON, keys) only in `.env` and secret files, out of git and logs.
- Encrypt backups with `backup-encrypt.sh` and store them, and the private key, on a separate host.
