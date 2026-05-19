#!/bin/bash
# Automated Rclone Backup for Vrenum
# Add to crontab: 0 2 * * * /path/to/backup_rclone.sh

set -e

# Configuration
PROJECT_DIR="/path/to/vrenum"
RCLONE_REMOTE="vrenum-backup"
BACKUP_BUCKET="vrenum-backups"
LOG_FILE="$PROJECT_DIR/logs/backup.log"

# Timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Starting backup..." | tee -a "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 1. Database Backup
echo "[$TIMESTAMP] Backing up database..." | tee -a "$LOG_FILE"
python3 scripts/backup_rclone.py --db-only 2>&1 | tee -a "$LOG_FILE"

# 2. User Uploads (incremental)
if [ -d "uploads/kyc" ]; then
    echo "[$TIMESTAMP] Syncing user uploads..." | tee -a "$LOG_FILE"
    rclone sync uploads/kyc/ "$RCLONE_REMOTE:$BACKUP_BUCKET/uploads/" \
        --progress \
        --log-file="$LOG_FILE" \
        --log-level INFO
fi

# 3. Archive old logs (monthly)
if [ -d "logs" ]; then
    MONTH=$(date +"%Y%m")
    echo "[$TIMESTAMP] Archiving logs..." | tee -a "$LOG_FILE"
    rclone copy logs/ "$RCLONE_REMOTE:$BACKUP_BUCKET/logs/$MONTH/" \
        --min-age 7d \
        --log-file="$LOG_FILE"
fi

# 4. Config backup (weekly on Sundays)
if [ $(date +%u) -eq 7 ] && [ -d "config" ]; then
    echo "[$TIMESTAMP] Backing up config..." | tee -a "$LOG_FILE"
    rclone sync config/ "$RCLONE_REMOTE:$BACKUP_BUCKET/config/" \
        --log-file="$LOG_FILE"
fi

# 5. Cleanup old local backups (keep 7 days)
find backups/ -name "vrenum_backup_*.sql.gz" -mtime +7 -delete 2>&1 | tee -a "$LOG_FILE"

# 6. Verify backup integrity
echo "[$TIMESTAMP] Verifying backup..." | tee -a "$LOG_FILE"
LATEST_BACKUP=$(rclone lsf "$RCLONE_REMOTE:$BACKUP_BUCKET/database/" | tail -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "[$TIMESTAMP] ✅ Latest backup: $LATEST_BACKUP" | tee -a "$LOG_FILE"
else
    echo "[$TIMESTAMP] ❌ No backup found!" | tee -a "$LOG_FILE"
    exit 1
fi

# 7. Send notification (optional)
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ Vrenum backup completed: $LATEST_BACKUP\"}"
fi

echo "[$TIMESTAMP] Backup complete!" | tee -a "$LOG_FILE"
