#!/bin/bash
# Emergency Backup Script for Render PostgreSQL
# Extracts ALL data before migration to new provider

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RENDER_DB_URL="postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v"
BACKUP_DIR="render_backup_$(date +%Y%m%d_%H%M%S)"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Render PostgreSQL Emergency Backup Script             ║${NC}"
echo -e "${BLUE}║     Namaskah SMS Platform - Data Extraction               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  This will backup ALL data from Render PostgreSQL${NC}"
echo -e "${YELLOW}⚠️  Backup directory: $BACKUP_DIR${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

echo -e "${GREEN}[1/8] Testing database connection...${NC}"
if psql "$RENDER_DB_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connection successful!${NC}"
else
    echo -e "${RED}❌ Cannot connect to Render database!${NC}"
    echo -e "${RED}   Database may already be deleted or inaccessible.${NC}"
    echo ""
    echo -e "${YELLOW}Checking for existing backups...${NC}"

    # Look for existing backups
    EXISTING_BACKUPS=$(find .. -name "render_backup_*" -o -name "namaskah_backup_*.sql*" -o -name "backup_*.sql*" 2>/dev/null | head -5)

    if [ -n "$EXISTING_BACKUPS" ]; then
        echo -e "${GREEN}Found existing backups:${NC}"
        echo "$EXISTING_BACKUPS"
        echo ""
        echo -e "${YELLOW}Use one of these backups for migration.${NC}"
    else
        echo -e "${RED}No existing backups found!${NC}"
        echo -e "${RED}If you have backups elsewhere, copy them to the project directory.${NC}"
    fi

    exit 1
fi
echo ""

echo -e "${GREEN}[2/8] Getting database statistics...${NC}"
# Get table counts
psql "$RENDER_DB_URL" -t -c "
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
" > table_statistics.txt

echo -e "${BLUE}Database Statistics:${NC}"
cat table_statistics.txt
echo ""

# Get total database size
DB_SIZE=$(psql "$RENDER_DB_URL" -t -c "SELECT pg_size_pretty(pg_database_size(current_database()));")
echo -e "${BLUE}Total Database Size: $DB_SIZE${NC}"
echo "$DB_SIZE" > database_size.txt
echo ""

echo -e "${GREEN}[3/8] Backing up database schema...${NC}"
pg_dump "$RENDER_DB_URL" --schema-only --no-owner --no-acl > schema_only.sql
SCHEMA_SIZE=$(du -h schema_only.sql | cut -f1)
echo -e "${GREEN}✅ Schema backup complete: $SCHEMA_SIZE${NC}"
echo ""

echo -e "${GREEN}[4/8] Backing up full database (SQL format)...${NC}"
pg_dump "$RENDER_DB_URL" --no-owner --no-acl --format=plain > full_backup.sql
FULL_SIZE=$(du -h full_backup.sql | cut -f1)
echo -e "${GREEN}✅ Full SQL backup complete: $FULL_SIZE${NC}"
echo ""

echo -e "${GREEN}[5/8] Creating compressed backup...${NC}"
gzip -c full_backup.sql > full_backup.sql.gz
COMPRESSED_SIZE=$(du -h full_backup.sql.gz | cut -f1)
echo -e "${GREEN}✅ Compressed backup complete: $COMPRESSED_SIZE${NC}"
echo ""

echo -e "${GREEN}[6/8] Backing up individual tables (CSV format)...${NC}"
mkdir -p csv_exports

# Get list of all tables
TABLES=$(psql "$RENDER_DB_URL" -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';")

for TABLE in $TABLES; do
    echo -e "  ${BLUE}→${NC} Exporting table: $TABLE"
    psql "$RENDER_DB_URL" -c "\COPY (SELECT * FROM $TABLE) TO 'csv_exports/${TABLE}.csv' WITH CSV HEADER;"
done

echo -e "${GREEN}✅ CSV exports complete${NC}"
echo ""

echo -e "${GREEN}[7/8] Backing up critical data (JSON format)...${NC}"
mkdir -p json_exports

# Export users
echo -e "  ${BLUE}→${NC} Exporting users..."
psql "$RENDER_DB_URL" -t -c "
SELECT json_agg(row_to_json(users.*))
FROM users;
" > json_exports/users.json

# Export transactions
echo -e "  ${BLUE}→${NC} Exporting transactions..."
psql "$RENDER_DB_URL" -t -c "
SELECT json_agg(row_to_json(transactions.*))
FROM transactions;
" > json_exports/transactions.json 2>/dev/null || echo "  ⚠️  Transactions table not found"

# Export verifications
echo -e "  ${BLUE}→${NC} Exporting verifications..."
psql "$RENDER_DB_URL" -t -c "
SELECT json_agg(row_to_json(verifications.*))
FROM verifications;
" > json_exports/verifications.json 2>/dev/null || echo "  ⚠️  Verifications table not found"

# Export subscription_tiers
echo -e "  ${BLUE}→${NC} Exporting subscription_tiers..."
psql "$RENDER_DB_URL" -t -c "
SELECT json_agg(row_to_json(subscription_tiers.*))
FROM subscription_tiers;
" > json_exports/subscription_tiers.json 2>/dev/null || echo "  ⚠️  Subscription_tiers table not found"

echo -e "${GREEN}✅ JSON exports complete${NC}"
echo ""

echo -e "${GREEN}[8/8] Creating backup manifest...${NC}"

# Create manifest file
cat > BACKUP_MANIFEST.txt << EOF
╔════════════════════════════════════════════════════════════╗
║          RENDER POSTGRESQL BACKUP MANIFEST                 ║
╚════════════════════════════════════════════════════════════╝

Backup Date: $TIMESTAMP
Database: Render PostgreSQL (Namaskah Production)
Database Size: $DB_SIZE

╔════════════════════════════════════════════════════════════╗
║                    BACKUP CONTENTS                         ║
╚════════════════════════════════════════════════════════════╝

1. FULL BACKUPS (Use these for migration)
   ├─ full_backup.sql         ($FULL_SIZE) - Complete database dump
   └─ full_backup.sql.gz      ($COMPRESSED_SIZE) - Compressed version

2. SCHEMA ONLY
   └─ schema_only.sql         ($SCHEMA_SIZE) - Database structure only

3. CSV EXPORTS (Individual tables)
   └─ csv_exports/
      $(ls -1 csv_exports/ | sed 's/^/      ├─ /')

4. JSON EXPORTS (Critical data)
   └─ json_exports/
      ├─ users.json
      ├─ transactions.json
      ├─ verifications.json
      └─ subscription_tiers.json

5. METADATA
   ├─ table_statistics.txt    - Row counts per table
   ├─ database_size.txt       - Total database size
   └─ BACKUP_MANIFEST.txt     - This file

╔════════════════════════════════════════════════════════════╗
║                  RESTORATION COMMANDS                      ║
╚════════════════════════════════════════════════════════════╝

To restore to new database:

1. Using full backup (recommended):
   psql "NEW_DATABASE_URL" < full_backup.sql

2. Using compressed backup:
   gunzip -c full_backup.sql.gz | psql "NEW_DATABASE_URL"

3. Using migration script:
   ./scripts/migrate_database.sh supabase "NEW_DATABASE_URL"

╔════════════════════════════════════════════════════════════╗
║                    TABLE STATISTICS                        ║
╚════════════════════════════════════════════════════════════╝

$(cat table_statistics.txt)

╔════════════════════════════════════════════════════════════╗
║                    VERIFICATION                            ║
╚════════════════════════════════════════════════════════════╝

To verify backup integrity:

1. Check file sizes:
   ls -lh *.sql*

2. Test SQL backup:
   head -100 full_backup.sql

3. Count tables:
   grep "CREATE TABLE" full_backup.sql | wc -l

4. Verify CSV exports:
   wc -l csv_exports/*.csv

╔════════════════════════════════════════════════════════════╗
║                    IMPORTANT NOTES                         ║
╚════════════════════════════════════════════════════════════╝

⚠️  KEEP THIS BACKUP SAFE!
   - Store in multiple locations (local + cloud)
   - Do NOT delete until migration is verified
   - Test restore before deleting Render database

✅ BACKUP PRIORITY:
   1. full_backup.sql.gz (primary - use for migration)
   2. full_backup.sql (secondary - uncompressed)
   3. csv_exports/ (tertiary - individual tables)
   4. json_exports/ (emergency - critical data only)

📋 NEXT STEPS:
   1. Verify backup files exist and are not empty
   2. Upload to cloud storage (Google Drive, OneDrive, etc.)
   3. Test restore to local database
   4. Proceed with migration to new provider

EOF

echo -e "${GREEN}✅ Backup manifest created${NC}"
echo ""

# Create checksums
echo -e "${GREEN}Creating checksums for verification...${NC}"
find . -type f \( -name "*.sql" -o -name "*.sql.gz" -o -name "*.csv" -o -name "*.json" \) -exec md5sum {} \; > CHECKSUMS.md5
echo -e "${GREEN}✅ Checksums created${NC}"
echo ""

# Summary
cd ..
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  BACKUP COMPLETE! ✅                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backup Location:${NC} $BACKUP_DIR"
echo -e "${BLUE}Total Size:${NC} $BACKUP_SIZE"
echo -e "${BLUE}Database Size:${NC} $DB_SIZE"
echo ""
echo -e "${YELLOW}📋 Backup Contents:${NC}"
echo -e "   ✅ Full SQL backup (compressed & uncompressed)"
echo -e "   ✅ Schema-only backup"
echo -e "   ✅ CSV exports (all tables)"
echo -e "   ✅ JSON exports (critical data)"
echo -e "   ✅ Statistics and manifest"
echo -e "   ✅ Checksums for verification"
echo ""
echo -e "${YELLOW}🔐 Security Reminder:${NC}"
echo -e "   ⚠️  Backup contains sensitive data (passwords, API keys, user info)"
echo -e "   ⚠️  Store securely and encrypt if uploading to cloud"
echo ""
echo -e "${GREEN}📤 Next Steps:${NC}"
echo -e "   1. Verify backup: ${BLUE}cat $BACKUP_DIR/BACKUP_MANIFEST.txt${NC}"
echo -e "   2. Upload to cloud: ${BLUE}rclone copy $BACKUP_DIR gdrive:Namaskah-Backups/${NC}"
echo -e "   3. Test restore locally: ${BLUE}psql LOCAL_DB < $BACKUP_DIR/full_backup.sql${NC}"
echo -e "   4. Migrate to Supabase: ${BLUE}./scripts/migrate_database.sh supabase \"NEW_URL\"${NC}"
echo ""
echo -e "${GREEN}✅ Your data is safe! Proceed with migration.${NC}"
echo ""
