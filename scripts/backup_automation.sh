#!/bin/bash

# Automated backup script for Namaskah SMS platform
# Run via cron: 0 */1 * * * /path/to/backup_automation.sh

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
S3_BUCKET="s3://namaskah-backups-us-east"

echo "Starting backup at $(date)"

# Database backup
echo "Backing up PostgreSQL database..."
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Redis backup
echo "Backing up Redis data..."
redis-cli --rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Configuration backup
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    /app/.env \
    /app/alembic.ini \
    /etc/nginx/nginx.conf

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_DIR/" "$S3_BUCKET/$(date +"%Y/%m/%d")/" --recursive

# Cleanup old local backups (keep 24 hours)
find "$BACKUP_DIR" -name "*.gz" -mtime +1 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +1 -delete

# Health check
curl -f http://localhost:8000/disaster-recovery/status || exit 1

echo "Backup completed successfully at $(date)"