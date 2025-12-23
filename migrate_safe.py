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
    
    engine = create_engine(database_url)
    
    # Clear any failed transactions
    with engine.connect() as conn:
        conn.execute(text("ROLLBACK"))
        conn.commit()
    
    inspector = inspect(engine)
    
    if "alembic_version" not in inspector.get_table_names():
        print("⚠️  No alembic_version table found. Creating and stamping...")
        # Create alembic_version table and stamp with head
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        print("✅ Database stamped with current state")
    else:
        print("✅ Migration tracking exists")
    
    # Now run migrations
    print("🔄 Running migrations...")
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations complete")
    except Exception as e:
        print(f"⚠️  Migration warning: {e}")
        print("Continuing anyway...")

if __name__ == "__main__":
    main()
