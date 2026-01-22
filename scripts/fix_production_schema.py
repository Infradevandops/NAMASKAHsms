#!/usr/bin/env python3
"""Fix production database schema - add missing columns."""
import os
import sys

from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    print(
        "Usage: DATABASE_URL='postgresql://...' python scripts/fix_production_schema.py"
    )
    sys.exit(1)

print(f"🔧 Connecting to database...")

# Add SSL parameters for Render PostgreSQL
connect_args = {}
if "render.com" in database_url or "postgres" in database_url:
    connect_args = {"sslmode": "require"}

engine = create_engine(database_url, connect_args=connect_args)

# SQL statements to add missing columns
sql_statements = [
    # Add bonus_sms_balance column
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS bonus_sms_balance FLOAT DEFAULT 0.0 NOT NULL;
    """,
    # Add monthly_quota_used column
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS monthly_quota_used FLOAT DEFAULT 0.0 NOT NULL;
    """,
    # Add monthly_quota_reset_date column
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS monthly_quota_reset_date TIMESTAMP;
    """,
    # Add other potentially missing columns from startup.py
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'USD';
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS tier_id VARCHAR(50) DEFAULT 'payg';
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS suspension_reason VARCHAR(500);
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS ban_reason VARCHAR(500);
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS deletion_reason VARCHAR(500);
    """,
]

try:
    with engine.connect() as conn:
        print("✅ Connected to database")

        for i, sql in enumerate(sql_statements, 1):
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Statement {i}/{len(sql_statements)} executed")
            except Exception as e:
                print(f"⚠️  Statement {i} skipped (column may exist): {str(e)[:100]}")

        print("\n✅ Schema update complete!")
        print("\nVerifying columns...")

        # Verify the columns exist
        result = conn.execute(
            text(
                """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN (
                'bonus_sms_balance', 
                'monthly_quota_used', 
                'monthly_quota_reset_date',
                'language',
                'currency',
                'tier_id',
                'is_active',
                'is_suspended',
                'is_banned',
                'is_deleted'
            )
            ORDER BY column_name;
        """
            )
        )

        columns = [row[0] for row in result]
        print(f"\n✅ Found {len(columns)} columns:")
        for col in columns:
            print(f"   - {col}")

        print("\n🎉 Production schema is now up to date!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
