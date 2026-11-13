#!/bin/bash
# Decrypt ./backups/db_backup.sql.bz2.ssl (from backup-encrypt.sh) with the PRIVATE key → ./backups/db_backup.sql.
# Run where the private key is (not on the bot server), then restore with backup-restore.sh.

ENCRYPTED_BACKUP_FILE="./backups/db_backup.sql.bz2.ssl"
DECRYPTED_COMPRESSED_FILE="./backups/db_backup.sql.bz2"
DATABASE_FILE="./backups/db_backup.sql"
PRIVATE_KEY="./keys/backup_key.pem"

echo "ENCRYPTED_BACKUP_FILE: $ENCRYPTED_BACKUP_FILE"
echo "DECRYPTED_COMPRESSED_FILE: $DECRYPTED_COMPRESSED_FILE"
echo "DATABASE_FILE: $DATABASE_FILE"
echo "PRIVATE_KEY: $PRIVATE_KEY"

echo "Decrypting the backup file..."
openssl smime -decrypt -in "$ENCRYPTED_BACKUP_FILE" -binary -inform DEM -inkey "$PRIVATE_KEY" -out "$DECRYPTED_COMPRESSED_FILE"
if [ $? -ne 0 ]; then
    echo "Decryption failed."
    exit 1
fi

echo "Decompressing the decrypted backup file..."
bzip2 -df "$DECRYPTED_COMPRESSED_FILE"
if [ $? -ne 0 ]; then
    echo "Decompression failed."
    exit 1
fi

# Now DATABASE_FILE should exist
if [ ! -f "$DATABASE_FILE" ]; then
    echo "Database file $DATABASE_FILE does not exist."
    exit 1
fi