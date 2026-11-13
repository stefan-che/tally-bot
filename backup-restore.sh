#!/bin/bash
# Restore a plain SQL dump (./backups/db_backup.sql, produced by backup-decrypt.sh) into the running Postgres.

source .env

PG_CONTAINER_NAME="${PG_CONTAINER_NAME:-ledger-pg}"
DATABASE_FILE="./backups/db_backup.sql"

echo "Restoring the database... '${PG_CONTAINER_NAME}'"
docker exec -i "$PG_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DATABASE_FILE"
if [ $? -ne 0 ]; then
    echo "Database restore failed."
    exit 1
fi

echo "Database restore completed successfully."
