#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/db_backup_20250116_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${POSTGRES_DB:-namaskah_prod}"
DB_USER="${POSTGRES_USER:-namaskah_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the database!"
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo "🔄 Restoring database from: $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME"
echo "✅ Database restored successfully"
