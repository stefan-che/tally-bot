#!/bin/bash
# Restore a custom-format dump (./backup.dump, produced by backup.sh) into the running Postgres.

source .env

PG_CONTAINER_NAME="${PG_CONTAINER_NAME:-ledger-pg}"
BACKUP_PATH_ON_SERVER="./backup.dump"
BACKUP_PATH_INSIDE_CONTAINER="/tmp/backup.dump"

# 1. Copy the dump into the container
echo "Copying backup to PostgreSQL container..."
docker cp "$BACKUP_PATH_ON_SERVER" "$PG_CONTAINER_NAME:$BACKUP_PATH_INSIDE_CONTAINER"
if [ $? -ne 0 ]; then
  echo "Error copying the backup file to the container!"
  exit 1
fi

# 2. Restore
echo "Restoring the PostgreSQL database from backup..."
docker exec -t "$PG_CONTAINER_NAME" pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists -v "$BACKUP_PATH_INSIDE_CONTAINER"
if [ $? -ne 0 ]; then
  echo "Error while restoring the database!"
  exit 1
fi

echo "Database restored successfully!"
