"""Fix production database - add missing idempotency_key column."""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Handle Render.com postgres:// -> postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

print("🔗 Connecting to database...")
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'verifications'
            AND column_name = 'idempotency_key'
        """))

        if result.fetchone():
            print("✅ idempotency_key column already exists")
        else:
            print("➕ Adding idempotency_key column...")
            conn.execute(text("ALTER TABLE verifications ADD COLUMN idempotency_key VARCHAR"))
            conn.execute(text("CREATE INDEX ix_verifications_idempotency_key ON verifications (idempotency_key)"))
            conn.commit()
            print("✅ Successfully added idempotency_key column and index")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)