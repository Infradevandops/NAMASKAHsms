#!/bin/bash
# Automated Database Backup Script
# Run daily via cron: 0 2 * * * /path/to/backup_automation.sh

set -e

# Change to project directory
cd "$(dirname "$0")/.."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run backup
python3 scripts/backup_database.py

# Optional: Upload to cloud storage (uncomment and configure)
# aws s3 cp backups/ s3://your-backup-bucket/ --recursive --exclude "*" --include "namaskah_backup_*.sql"

echo "Backup automation completed at $(date)"