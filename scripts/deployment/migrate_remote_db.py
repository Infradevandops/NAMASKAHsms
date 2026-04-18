#!/usr/bin/env python3
"""
Remote Database Migration Script
Run migrations on production database from your local machine
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_migration():
    """Run Alembic migration on remote database."""
    
    print("🔄 Remote Database Migration")
    print("=" * 50)
    print()
    
    # Check for DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set")
        print()
        print("Please set your production database URL:")
        print()
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        print()
        print("Or run with:")
        print()
        print("  DATABASE_URL='your_db_url' python scripts/deployment/migrate_remote_db.py")
        print()
        return False
    
    # Mask password in display
    display_url = db_url
    if "@" in db_url and "://" in db_url:
        parts = db_url.split("://")
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            if "@" in rest:
                creds, host = rest.split("@", 1)
                if ":" in creds:
                    user = creds.split(":")[0]
                    display_url = f"{protocol}://{user}:****@{host}"
    
    print(f"📊 Database: {display_url}")
    print()
    
    # Import alembic
    try:
        from alembic.config import Config
        from alembic import command
    except ImportError:
        print("❌ ERROR: Alembic not installed")
        print()
        print("Install dependencies:")
        print("  pip install -r requirements.txt")
        print()
        return False
    
    # Set up Alembic config
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    try:
        print("🔍 Checking current migration status...")
        command.current(alembic_cfg, verbose=True)
        print()
        
        print("⬆️  Running migrations...")
        command.upgrade(alembic_cfg, "head")
        print()
        
        print("✅ Migration completed successfully!")
        print()
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Restart your Render service")
        print("2. Test login at https://namaskahsms.onrender.com/login")
        print("3. Verify all features are working")
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Migration failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your DATABASE_URL is correct")
        print("2. Ensure database is accessible from your network")
        print("3. Verify database user has ALTER TABLE permissions")
        print()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
