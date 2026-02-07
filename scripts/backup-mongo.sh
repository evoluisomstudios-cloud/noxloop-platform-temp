#!/bin/bash
# MongoDB Backup Script for NOXLOOP

BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER="noxloop-mongodb"
DB_NAME="noxloop_db"

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# Create backup
docker exec $CONTAINER mongodump \
  --username admin \
  --password changeme \
  --authenticationDatabase admin \
  --db $DB_NAME \
  --archive=/data/backup_$DATE.archive

# Copy backup to host
docker cp $CONTAINER:/data/backup_$DATE.archive $BACKUP_DIR/

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.archive

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.archive.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.archive.gz"
echo "Size: $(du -h $BACKUP_DIR/backup_$DATE.archive.gz | cut -f1)"
