#!/usr/bin/env python3
"""Fix missing columns in production database."""
import os
import sys

from sqlalchemy import create_engine, text


def fix_schema():
    """Add missing columns to users table."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    print("🔗 Connecting to database...")
    engine = create_engine(database_url)

    sql_commands = [
        # Original subscription tier columns
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'freemium' NOT NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_upgraded_at TIMESTAMP;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_expires_at TIMESTAMP;",
        "CREATE INDEX IF NOT EXISTS ix_users_subscription_tier ON users(subscription_tier);",
        # New missing columns (2025-12-29)
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'USD';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_id VARCHAR(50);",
    ]

    with engine.connect() as conn:
        for sql in sql_commands:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ {sql[:60]}...")
            except Exception as e:
                print(f"⚠️  {sql[:60]}... - {e}")

    print("\n✅ Schema fix completed")


if __name__ == "__main__":
    fix_schema()