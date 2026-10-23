#!/bin/bash
# VRENUM SMS - Database Backup Script
# Usage: ./scripts/backup-db.sh
# Add to cron: 0 2 * * * /home/vrenum/app/scripts/backup-db.sh

set -e

BACKUP_DIR="/home/vrenum/app/backups/db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="vrenum_backup_${DATE}.sql.gz"
KEEP_DAYS=7

echo "📦 Starting database backup..."

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Dump database
docker compose exec -T db pg_dump -U ${POSTGRES_USER:-vrenum} ${POSTGRES_DB:-vrenum} | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Check if backup was successful
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ] && [ -s "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "✅ Backup created: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Remove old backups
echo "🧹 Cleaning old backups (keeping last $KEEP_DAYS days)..."
find $BACKUP_DIR -name "vrenum_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

# List current backups
echo ""
echo "Current backups:"
ls -lh $BACKUP_DIR/*.sql.gz 2>/dev/null || echo "No backups found"
