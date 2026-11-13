#!/bin/bash
# Plain backup: pg_dump (custom format) → ./backup.dump, optionally sent to a Telegram chat.
#
# CRONTAB (daily at 03:00):
#   0 3 * * * cd /opt/tally-bot && ./backup.sh >> /opt/tally-bot/backup.log 2>&1
#
# chmod +x backup.sh

source .env

PG_CONTAINER_NAME="${PG_CONTAINER_NAME:-ledger-pg}"
BACKUP_PATH_INSIDE_CONTAINER="/tmp/backup.dump"
BACKUP_PATH_ON_SERVER="./backup.dump"

# 1. Dump inside the PostgreSQL container
echo "Creating PostgreSQL backup..."
docker exec -t "$PG_CONTAINER_NAME" pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$BACKUP_PATH_INSIDE_CONTAINER"
if [ $? -ne 0 ]; then
  echo "Backup failed!"
  exit 1
fi

# 2. Copy to the host
echo "Copying backup to local server..."
docker cp "$PG_CONTAINER_NAME:$BACKUP_PATH_INSIDE_CONTAINER" "$BACKUP_PATH_ON_SERVER"
if [ $? -ne 0 ]; then
  echo "Failed to copy the backup!"
  exit 1
fi
docker exec "$PG_CONTAINER_NAME" rm -f "$BACKUP_PATH_INSIDE_CONTAINER"
echo "Backup copied to $BACKUP_PATH_ON_SERVER"

# 3. Optional: send to Telegram
if [ -n "$BACKUP_CHAT_ID" ]; then
  echo "Sending backup to Telegram..."
  curl -sS -F chat_id="$BACKUP_CHAT_ID" \
       -F document=@"$BACKUP_PATH_ON_SERVER" \
       -F caption="Database backup: $POSTGRES_DB" \
       "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" > /dev/null
  if [ $? -ne 0 ]; then
    echo "Failed to send the backup to Telegram!"
    exit 1
  fi
fi

echo "Backup completed."
