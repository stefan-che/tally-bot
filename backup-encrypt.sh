#!/bin/bash
# Encrypted backup: pg_dump (plain SQL) → bzip2 → openssl smime (public key) → ./backups/db_backup.sql.bz2.ssl,
# optionally sent to a Telegram chat. Decrypt with backup-decrypt.sh, restore with backup-restore.sh.
#
# Key pair (keep the private key OFF the server):
#   openssl req -x509 -nodes -days 3650 -newkey rsa:4096 -subj "/CN=ledger-backup" \
#     -keyout backup_key.pem -out backup_key.pem.pub
#   mkdir -p keys && mv backup_key.pem.pub keys/      # only the public part on the server
#
# CRONTAB (daily at 03:00):
#   0 3 * * * cd /opt/tally-bot && ./backup-encrypt.sh >> /opt/tally-bot/backups/cron.log 2>&1

source .env

DB_NAME=${POSTGRES_DB:-"ledger"}
DB_USER=${POSTGRES_USER:-"ledger"}
DB_CONTAINER="${PG_CONTAINER_NAME:-ledger-pg}"
BACKUP_DIR="backups"
PUBLIC_KEY="./keys/backup_key.pem.pub"

echo "DB: $DB_NAME"
echo "User: $DB_USER"
echo "Container: $DB_CONTAINER"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d%H%M%S")

BACKUP_FILE="db_backup.sql"
ENCRYPTED_BACKUP_FILE="db_backup.sql.bz2.ssl"
BACKUP_PATH_INSIDE_CONTAINER="/tmp/$BACKUP_FILE"
BACKUP_PATH_ON_HOST="$BACKUP_DIR/$BACKUP_FILE"

echo "Starting backup for container: $DB_CONTAINER, database: $DB_NAME"

# Step 1: pg_dump inside the container
echo "Creating backup inside the container..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" -f "$BACKUP_PATH_INSIDE_CONTAINER"
if [ $? -ne 0 ]; then
    echo "Backup failed during pg_dump." >> "$BACKUP_DIR/backup.log"
    exit 1
fi

# Step 2: copy to the host
echo "Copying backup file from container to host..."
docker cp "$DB_CONTAINER":"$BACKUP_PATH_INSIDE_CONTAINER" "$BACKUP_PATH_ON_HOST"
if [ $? -ne 0 ]; then
    echo "Failed to copy the backup file from the container." >> "$BACKUP_DIR/backup.log"
    docker exec "$DB_CONTAINER" rm "$BACKUP_PATH_INSIDE_CONTAINER"
    exit 1
fi
docker exec "$DB_CONTAINER" rm "$BACKUP_PATH_INSIDE_CONTAINER"

# Step 3: compress
echo "Compressing the backup file..."
bzip2 -f "$BACKUP_PATH_ON_HOST"
if [ $? -ne 0 ]; then
    echo "Compression failed." >> "$BACKUP_DIR/backup.log"
    exit 1
fi

# Step 4: encrypt with the public key
echo "Encrypting the backup file..."
openssl smime -encrypt -aes256 -binary -outform DEM -in "$BACKUP_PATH_ON_HOST.bz2" -out "$BACKUP_DIR/$ENCRYPTED_BACKUP_FILE" "$PUBLIC_KEY"
if [ $? -ne 0 ]; then
    echo "Encryption failed."
    exit 1
fi

# Remove the unencrypted compressed backup (leave only the encrypted one)
rm "$BACKUP_PATH_ON_HOST.bz2"

echo "Backup completed at $TIMESTAMP" >> "$BACKUP_DIR/backup.log"
echo "Encrypted backup stored at $BACKUP_DIR/$ENCRYPTED_BACKUP_FILE"

# Step 5 (optional): send to Telegram
if [ -n "$BACKUP_CHAT_ID" ]; then
    echo "Sending backup to Telegram..."
    curl -sS -F chat_id="$BACKUP_CHAT_ID" \
         -F document=@"$BACKUP_DIR/$ENCRYPTED_BACKUP_FILE" \
         -F caption="Database backup: $DB_NAME" \
         "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" > /dev/null
fi
