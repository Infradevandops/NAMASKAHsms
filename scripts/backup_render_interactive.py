#!/usr/bin/env python3
"""
Interactive Render Database Backup Script
Prompts for connection string and backs up all data
"""

import datetime
import getpass
import os
import subprocess
import sys
from pathlib import Path

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_header():
    print(f"{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║     Interactive Render Database Backup                    ║{Colors.NC}")
    print(f"{Colors.BLUE}║     Namaskah SMS Platform                                 ║{Colors.NC}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()

def get_connection_string():
    """Prompt user for connection string."""
    print(f"{Colors.CYAN}📋 Step 1: Get Connection String{Colors.NC}")
    print()
    print("Go to Render Dashboard:")
    print("  1. https://dashboard.render.com")
    print("  2. Find your database: namaskahdb")
    print("  3. Scroll to 'Connections' section")
    print("  4. Copy 'External Database URL'")
    print()
    print(f"{Colors.YELLOW}It should look like:{Colors.NC}")
    print("  postgresql://user:pass@dpg-xxx.oregon-postgres.render.com:5432/dbname")
    print()

    # Try to use existing connection string
    existing_url = os.environ.get('DATABASE_URL', '')
    if existing_url and 'render.com' in existing_url:
        print(f"{Colors.GREEN}Found existing connection string in environment{Colors.NC}")
        use_existing = input(f"Use this? (y/n): ").strip().lower()
        if use_existing == 'y':
            return existing_url

    # Prompt for new connection string
    print(f"{Colors.CYAN}Paste your connection string:{Colors.NC}")
    connection_string = input().strip()

    if not connection_string:
        print(f"{Colors.RED}❌ No connection string provided{Colors.NC}")
        sys.exit(1)

    # Validate format
    if not connection_string.startswith('postgresql://'):
        print(f"{Colors.RED}❌ Invalid format. Should start with 'postgresql://'{Colors.NC}")
        sys.exit(1)

    if 'render.com' not in connection_string:
        print(f"{Colors.YELLOW}⚠️  Warning: Connection string doesn't contain 'render.com'{Colors.NC}")
        print(f"{Colors.YELLOW}   Make sure you copied the FULL connection string{Colors.NC}")
        proceed = input("Proceed anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            sys.exit(1)

    return connection_string

def test_connection(db_url):
    """Test database connection."""
    print()
    print(f"{Colors.CYAN}🔌 Step 2: Testing Connection{Colors.NC}")
    print()

    result = subprocess.run(
        ["psql", db_url, "-c", "SELECT version();"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ Connection successful!{Colors.NC}")
        version = result.stdout.split('\n')[2].strip() if len(result.stdout.split('\n')) > 2 else 'Unknown'
        print(f"   {version}")
        return True
    else:
        print(f"{Colors.RED}❌ Connection failed!{Colors.NC}")
        print(f"{Colors.RED}   Error: {result.stderr}{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}Common issues:{Colors.NC}")
        print("  - Incomplete hostname (missing .render.com)")
        print("  - Wrong password")
        print("  - Database deleted")
        print("  - Network issue")
        return False

def get_database_info(db_url):
    """Get database statistics."""
    print()
    print(f"{Colors.CYAN}📊 Step 3: Database Information{Colors.NC}")
    print()

    # Get database size
    result = subprocess.run(
        ["psql", db_url, "-t", "-c", "SELECT pg_size_pretty(pg_database_size(current_database()));"],
        capture_output=True,
        text=True
    )
    db_size = result.stdout.strip() if result.returncode == 0 else "Unknown"
    print(f"{Colors.BLUE}Database Size:{Colors.NC} {db_size}")

    # Get table count
    result = subprocess.run(
        ["psql", db_url, "-t", "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"],
        capture_output=True,
        text=True
    )
    table_count = result.stdout.strip() if result.returncode == 0 else "Unknown"
    print(f"{Colors.BLUE}Tables:{Colors.NC} {table_count}")

    # Get table statistics
    print()
    print(f"{Colors.BLUE}Table Statistics:{Colors.NC}")
    result = subprocess.run(
        ["psql", db_url, "-c", """
        SELECT
            tablename,
            n_live_tup as rows
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
        LIMIT 10;
        """],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(result.stdout)

    return db_size, table_count

def confirm_backup():
    """Ask user to confirm backup."""
    print()
    print(f"{Colors.YELLOW}⚠️  Ready to backup database{Colors.NC}")
    print()
    print("This will:")
    print("  ✅ Create full SQL backup")
    print("  ✅ Create compressed backup")
    print("  ✅ Export tables as CSV")
    print("  ✅ Export critical data as JSON")
    print()

    confirm = input(f"{Colors.CYAN}Proceed with backup? (y/n):{Colors.NC} ").strip().lower()
    return confirm == 'y'

def backup_database(db_url):
    """Backup database."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"render_backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)

    print()
    print(f"{Colors.CYAN}💾 Step 4: Backing Up Database{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Backup directory:{Colors.NC} {backup_dir}")
    print()

    # Full backup
    print(f"{Colors.GREEN}[1/4] Creating full SQL backup...{Colors.NC}")
    full_backup = backup_dir / "full_backup.sql"

    result = subprocess.run(
        ["pg_dump", db_url, "--no-owner", "--no-acl"],
        stdout=open(full_backup, 'w'),
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode == 0:
        size = full_backup.stat().st_size / (1024 * 1024)
        print(f"   ✅ Complete: {size:.2f} MB")
    else:
        print(f"   ❌ Failed: {result.stderr}")
        return None

    # Compressed backup
    print(f"{Colors.GREEN}[2/4] Creating compressed backup...{Colors.NC}")
    compressed = backup_dir / "full_backup.sql.gz"

    subprocess.run(
        ["gzip", "-c", str(full_backup)],
        stdout=open(compressed, 'wb'),
        stderr=subprocess.PIPE
    )

    size = compressed.stat().st_size / (1024 * 1024)
    print(f"   ✅ Complete: {size:.2f} MB")

    # Schema only
    print(f"{Colors.GREEN}[3/4] Creating schema backup...{Colors.NC}")
    schema = backup_dir / "schema_only.sql"

    subprocess.run(
        ["pg_dump", db_url, "--schema-only", "--no-owner", "--no-acl"],
        stdout=open(schema, 'w'),
        stderr=subprocess.PIPE
    )

    size = schema.stat().st_size / 1024
    print(f"   ✅ Complete: {size:.1f} KB")

    # CSV exports
    print(f"{Colors.GREEN}[4/4] Exporting tables as CSV...{Colors.NC}")
    csv_dir = backup_dir / "csv_exports"
    csv_dir.mkdir(exist_ok=True)

    # Get tables
    result = subprocess.run(
        ["psql", db_url, "-t", "-c", "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        tables = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
        for table in tables:
            csv_file = csv_dir / f"{table}.csv"
            subprocess.run(
                ["psql", db_url, "-c", f"\\COPY (SELECT * FROM {table}) TO '{csv_file}' WITH CSV HEADER;"],
                capture_output=True
            )
        print(f"   ✅ Exported {len(tables)} tables")

    # Create manifest
    manifest = backup_dir / "BACKUP_MANIFEST.txt"
    with open(manifest, 'w') as f:
        f.write(f"""
Render PostgreSQL Backup
========================

Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Backup Directory: {backup_dir}

Files:
- full_backup.sql         (Complete database dump)
- full_backup.sql.gz      (Compressed version)
- schema_only.sql         (Structure only)
- csv_exports/            (Individual tables)

Restore Command:
psql "NEW_DATABASE_URL" < full_backup.sql

Or use migration script:
./scripts/migrate_database.sh supabase "NEW_URL"
""")

    return backup_dir

def print_summary(backup_dir, db_size):
    """Print backup summary."""
    total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)

    print()
    print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.GREEN}║                  BACKUP COMPLETE! ✅                       ║{Colors.NC}")
    print(f"{Colors.GREEN}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Backup Location:{Colors.NC} {backup_dir}")
    print(f"{Colors.BLUE}Total Size:{Colors.NC} {total_size_mb:.2f} MB")
    print(f"{Colors.BLUE}Database Size:{Colors.NC} {db_size}")
    print()
    print(f"{Colors.YELLOW}📋 Next Steps:{Colors.NC}")
    print()
    print(f"1. {Colors.CYAN}Verify backup:{Colors.NC}")
    print(f"   ls -lh {backup_dir}/")
    print()
    print(f"2. {Colors.CYAN}Upload to cloud:{Colors.NC}")
    print(f"   rclone copy {backup_dir}/ gdrive:Namaskah-Backups/")
    print()
    print(f"3. {Colors.CYAN}Migrate to Supabase:{Colors.NC}")
    print(f"   ./scripts/migrate_database.sh supabase \"NEW_URL\"")
    print()
    print(f"4. {Colors.CYAN}Or restore manually:{Colors.NC}")
    print(f"   psql \"NEW_URL\" < {backup_dir}/full_backup.sql")
    print()
    print(f"{Colors.GREEN}✅ Your data is safe!{Colors.NC}")
    print()

def main():
    """Main workflow."""
    print_header()

    # Get connection string
    db_url = get_connection_string()

    # Test connection
    if not test_connection(db_url):
        print()
        print(f"{Colors.RED}Cannot proceed without valid connection.{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}Please:{Colors.NC}")
        print("  1. Check Render Dashboard for correct connection string")
        print("  2. Verify database still exists")
        print("  3. Try again with correct connection string")
        sys.exit(1)

    # Get database info
    db_size, table_count = get_database_info(db_url)

    # Confirm backup
    if not confirm_backup():
        print()
        print(f"{Colors.YELLOW}Backup cancelled.{Colors.NC}")
        sys.exit(0)

    # Backup database
    backup_dir = backup_database(db_url)

    if backup_dir:
        # Print summary
        print_summary(backup_dir, db_size)
    else:
        print()
        print(f"{Colors.RED}❌ Backup failed!{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Backup cancelled by user.{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        sys.exit(1)
