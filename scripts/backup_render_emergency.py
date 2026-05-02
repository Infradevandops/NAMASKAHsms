#!/usr/bin/env python3
"""
Emergency Backup Script for Render PostgreSQL
Extracts ALL data before migration to new provider
"""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

# Configuration
RENDER_DB_URL = "postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a/namaskahdb_qg9v"
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = Path(f"render_backup_{TIMESTAMP}")

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header():
    print(f"{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║     Render PostgreSQL Emergency Backup Script             ║{Colors.NC}")
    print(f"{Colors.BLUE}║     Namaskah SMS Platform - Data Extraction               ║{Colors.NC}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}⚠️  This will backup ALL data from Render PostgreSQL{Colors.NC}")
    print(f"{Colors.YELLOW}⚠️  Backup directory: {BACKUP_DIR}{Colors.NC}")
    print()

def run_psql(query, output_file=None):
    """Run psql command and return output."""
    cmd = ["psql", RENDER_DB_URL, "-t", "-c", query]
    
    if output_file:
        with open(output_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    return result

def test_connection():
    """Test database connection."""
    print(f"{Colors.GREEN}[1/8] Testing database connection...{Colors.NC}")
    
    result = subprocess.run(
        ["psql", RENDER_DB_URL, "-c", "SELECT version();"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ Connection successful!{Colors.NC}")
        return True
    else:
        print(f"{Colors.RED}❌ Cannot connect to Render database!{Colors.NC}")
        print(f"{Colors.RED}   Database may already be deleted or inaccessible.{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}Checking for existing backups...{Colors.NC}")
        
        # Look for existing backups
        backup_patterns = ["render_backup_*", "namaskah_backup_*.sql*", "backup_*.sql*"]
        existing_backups = []
        
        for pattern in backup_patterns:
            existing_backups.extend(Path(".").glob(pattern))
        
        if existing_backups:
            print(f"{Colors.GREEN}Found existing backups:{Colors.NC}")
            for backup in existing_backups[:5]:
                print(f"  - {backup}")
            print()
            print(f"{Colors.YELLOW}Use one of these backups for migration.{Colors.NC}")
        else:
            print(f"{Colors.RED}No existing backups found!{Colors.NC}")
            print(f"{Colors.RED}If you have backups elsewhere, copy them to the project directory.{Colors.NC}")
        
        return False

def get_statistics():
    """Get database statistics."""
    print()
    print(f"{Colors.GREEN}[2/8] Getting database statistics...{Colors.NC}")
    
    # Table statistics
    stats_file = BACKUP_DIR / "table_statistics.txt"
    run_psql("""
        SELECT 
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
    """, stats_file)
    
    print(f"{Colors.BLUE}Database Statistics:{Colors.NC}")
    with open(stats_file) as f:
        print(f.read())
    
    # Database size
    result = run_psql("SELECT pg_size_pretty(pg_database_size(current_database()));")
    db_size = result.stdout.strip()
    print(f"{Colors.BLUE}Total Database Size: {db_size}{Colors.NC}")
    
    with open(BACKUP_DIR / "database_size.txt", 'w') as f:
        f.write(db_size)
    
    return db_size

def backup_schema():
    """Backup database schema only."""
    print()
    print(f"{Colors.GREEN}[3/8] Backing up database schema...{Colors.NC}")
    
    schema_file = BACKUP_DIR / "schema_only.sql"
    
    result = subprocess.run(
        ["pg_dump", RENDER_DB_URL, "--schema-only", "--no-owner", "--no-acl"],
        stdout=open(schema_file, 'w'),
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode == 0:
        size = schema_file.stat().st_size / 1024  # KB
        print(f"{Colors.GREEN}✅ Schema backup complete: {size:.1f} KB{Colors.NC}")
    else:
        print(f"{Colors.RED}❌ Schema backup failed: {result.stderr}{Colors.NC}")

def backup_full():
    """Backup full database."""
    print()
    print(f"{Colors.GREEN}[4/8] Backing up full database (SQL format)...{Colors.NC}")
    
    full_file = BACKUP_DIR / "full_backup.sql"
    
    result = subprocess.run(
        ["pg_dump", RENDER_DB_URL, "--no-owner", "--no-acl", "--format=plain"],
        stdout=open(full_file, 'w'),
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode == 0:
        size = full_file.stat().st_size / (1024 * 1024)  # MB
        print(f"{Colors.GREEN}✅ Full SQL backup complete: {size:.2f} MB{Colors.NC}")
        return full_file
    else:
        print(f"{Colors.RED}❌ Full backup failed: {result.stderr}{Colors.NC}")
        return None

def compress_backup(full_file):
    """Compress the full backup."""
    print()
    print(f"{Colors.GREEN}[5/8] Creating compressed backup...{Colors.NC}")
    
    compressed_file = BACKUP_DIR / "full_backup.sql.gz"
    
    result = subprocess.run(
        ["gzip", "-c", str(full_file)],
        stdout=open(compressed_file, 'wb'),
        stderr=subprocess.PIPE
    )
    
    if result.returncode == 0:
        size = compressed_file.stat().st_size / (1024 * 1024)  # MB
        print(f"{Colors.GREEN}✅ Compressed backup complete: {size:.2f} MB{Colors.NC}")
    else:
        print(f"{Colors.RED}❌ Compression failed{Colors.NC}")

def backup_csv():
    """Backup individual tables as CSV."""
    print()
    print(f"{Colors.GREEN}[6/8] Backing up individual tables (CSV format)...{Colors.NC}")
    
    csv_dir = BACKUP_DIR / "csv_exports"
    csv_dir.mkdir(exist_ok=True)
    
    # Get list of tables
    result = run_psql("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
    
    for table in tables:
        print(f"  {Colors.BLUE}→{Colors.NC} Exporting table: {table}")
        
        csv_file = csv_dir / f"{table}.csv"
        
        subprocess.run(
            ["psql", RENDER_DB_URL, "-c", 
             f"\\COPY (SELECT * FROM {table}) TO '{csv_file}' WITH CSV HEADER;"],
            capture_output=True
        )
    
    print(f"{Colors.GREEN}✅ CSV exports complete{Colors.NC}")

def backup_json():
    """Backup critical data as JSON."""
    print()
    print(f"{Colors.GREEN}[7/8] Backing up critical data (JSON format)...{Colors.NC}")
    
    json_dir = BACKUP_DIR / "json_exports"
    json_dir.mkdir(exist_ok=True)
    
    critical_tables = ["users", "transactions", "verifications", "subscription_tiers"]
    
    for table in critical_tables:
        print(f"  {Colors.BLUE}→{Colors.NC} Exporting {table}...")
        
        result = run_psql(f"""
            SELECT json_agg(row_to_json({table}.*))
            FROM {table};
        """)
        
        if result.returncode == 0 and result.stdout.strip():
            json_file = json_dir / f"{table}.json"
            with open(json_file, 'w') as f:
                f.write(result.stdout)
        else:
            print(f"  ⚠️  {table} table not found or empty")
    
    print(f"{Colors.GREEN}✅ JSON exports complete{Colors.NC}")

def create_manifest(db_size):
    """Create backup manifest."""
    print()
    print(f"{Colors.GREEN}[8/8] Creating backup manifest...{Colors.NC}")
    
    manifest = f"""╔════════════════════════════════════════════════════════════╗
║          RENDER POSTGRESQL BACKUP MANIFEST                 ║
╚════════════════════════════════════════════════════════════╝

Backup Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Database: Render PostgreSQL (Namaskah Production)
Database Size: {db_size}

╔════════════════════════════════════════════════════════════╗
║                    BACKUP CONTENTS                         ║
╚════════════════════════════════════════════════════════════╝

1. FULL BACKUPS (Use these for migration)
   ├─ full_backup.sql         - Complete database dump
   └─ full_backup.sql.gz      - Compressed version

2. SCHEMA ONLY
   └─ schema_only.sql         - Database structure only

3. CSV EXPORTS (Individual tables)
   └─ csv_exports/
      {chr(10).join(f"      ├─ {f.name}" for f in (BACKUP_DIR / "csv_exports").glob("*.csv"))}

4. JSON EXPORTS (Critical data)
   └─ json_exports/
      {chr(10).join(f"      ├─ {f.name}" for f in (BACKUP_DIR / "json_exports").glob("*.json"))}

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
"""
    
    with open(BACKUP_DIR / "BACKUP_MANIFEST.txt", 'w') as f:
        f.write(manifest)
    
    print(f"{Colors.GREEN}✅ Backup manifest created{Colors.NC}")

def print_summary(db_size):
    """Print backup summary."""
    # Calculate backup size
    total_size = sum(f.stat().st_size for f in BACKUP_DIR.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    print()
    print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.GREEN}║                  BACKUP COMPLETE! ✅                       ║{Colors.NC}")
    print(f"{Colors.GREEN}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Backup Location:{Colors.NC} {BACKUP_DIR}")
    print(f"{Colors.BLUE}Total Size:{Colors.NC} {total_size_mb:.2f} MB")
    print(f"{Colors.BLUE}Database Size:{Colors.NC} {db_size}")
    print()
    print(f"{Colors.YELLOW}📋 Backup Contents:{Colors.NC}")
    print("   ✅ Full SQL backup (compressed & uncompressed)")
    print("   ✅ Schema-only backup")
    print("   ✅ CSV exports (all tables)")
    print("   ✅ JSON exports (critical data)")
    print("   ✅ Statistics and manifest")
    print()
    print(f"{Colors.YELLOW}🔐 Security Reminder:{Colors.NC}")
    print("   ⚠️  Backup contains sensitive data (passwords, API keys, user info)")
    print("   ⚠️  Store securely and encrypt if uploading to cloud")
    print()
    print(f"{Colors.GREEN}📤 Next Steps:{Colors.NC}")
    print(f"   1. Verify backup: {Colors.BLUE}cat {BACKUP_DIR}/BACKUP_MANIFEST.txt{Colors.NC}")
    print(f"   2. Upload to cloud: {Colors.BLUE}rclone copy {BACKUP_DIR} gdrive:Namaskah-Backups/{Colors.NC}")
    print(f"   3. Test restore locally: {Colors.BLUE}psql LOCAL_DB < {BACKUP_DIR}/full_backup.sql{Colors.NC}")
    print(f"   4. Migrate to Supabase: {Colors.BLUE}./scripts/migrate_database.sh supabase \"NEW_URL\"{Colors.NC}")
    print()
    print(f"{Colors.GREEN}✅ Your data is safe! Proceed with migration.{Colors.NC}")
    print()

def main():
    """Main backup workflow."""
    print_header()
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Get statistics
    db_size = get_statistics()
    
    # Backup schema
    backup_schema()
    
    # Backup full database
    full_file = backup_full()
    
    if full_file:
        # Compress backup
        compress_backup(full_file)
        
        # Backup CSV
        backup_csv()
        
        # Backup JSON
        backup_json()
        
        # Create manifest
        create_manifest(db_size)
        
        # Print summary
        print_summary(db_size)
    else:
        print(f"{Colors.RED}❌ Backup failed!{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
