#!/bin/bash
# ============================================
# DigiForge Backup Script
# Run: ./backup.sh
# ============================================

set -e

BACKUP_DIR="${BACKUP_DIR:-/opt/backups/digiforge}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Backup MongoDB
docker exec digiforge-mongodb mongodump --out /backup --quiet 2>/dev/null || {
    echo "[$(date)] ERROR: Failed to create MongoDB dump"
    exit 1
}

docker cp digiforge-mongodb:/backup "$BACKUP_DIR/mongodb_$DATE"

# Comprimir
cd "$BACKUP_DIR"
tar -czf "digiforge_backup_$DATE.tar.gz" "mongodb_$DATE"
rm -rf "mongodb_$DATE"

# Limpar dentro do container
docker exec digiforge-mongodb rm -rf /backup 2>/dev/null || true

# Remover backups antigos
find "$BACKUP_DIR" -name "digiforge_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_DIR/digiforge_backup_$DATE.tar.gz" | cut -f1)
echo "[$(date)] Backup completed: digiforge_backup_$DATE.tar.gz ($BACKUP_SIZE)"
