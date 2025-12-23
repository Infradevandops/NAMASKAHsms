#!/usr/bin/env python3
"""Safe migration script that handles existing databases."""
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
import os

def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    # Check if alembic_version table exists
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    if "alembic_version" not in inspector.get_table_names():
        print("⚠️  No alembic_version table found. Stamping database...")
        # Database exists but no migration tracking - stamp it
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "cb2a98627849")  # Latest merge head
        print("✅ Database stamped with current state")
    else:
        print("✅ Migration tracking exists")
    
    # Now run migrations
    print("🔄 Running migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations complete")

if __name__ == "__main__":
    main()
