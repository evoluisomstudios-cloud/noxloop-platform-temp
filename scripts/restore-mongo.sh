#!/bin/bash
# MongoDB Restore Script for NOXLOOP

if [ -z "$1" ]; then
    echo "Usage: ./restore-mongo.sh backup_filename.archive.gz"
    exit 1
fi

BACKUP_FILE=$1
CONTAINER="noxloop-mongodb"

if [ ! -f "/app/backups/$BACKUP_FILE" ]; then
    echo "Backup file not found: /app/backups/$BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will restore the database from backup."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c /app/backups/$BACKUP_FILE > /tmp/restore.archive
    RESTORE_FILE=/tmp/restore.archive
else
    RESTORE_FILE=/app/backups/$BACKUP_FILE
fi

# Copy to container
docker cp $RESTORE_FILE $CONTAINER:/data/restore.archive

# Restore
docker exec $CONTAINER mongorestore \
  --username admin \
  --password changeme \
  --authenticationDatabase admin \
  --drop \
  --archive=/data/restore.archive

# Cleanup
rm -f /tmp/restore.archive

echo "Restore completed!"
