#!/bin/bash
# Add to cron on the host (every 5 minutes):
#   */5 * * * * /opt/tally-bot/wallet_sync.sh >> /var/log/wallet_sync.log 2>&1
#
# Or with logrotate rotation, or simply:
#   */5 * * * * /opt/tally-bot/wallet_sync.sh

CONTAINER="${BOT_CONTAINER:-tally-bot}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "[wallet_sync] container '${CONTAINER}' is not running — skipping"
    exit 1
fi

docker exec "$CONTAINER" python3 /app/wallet_sync.py