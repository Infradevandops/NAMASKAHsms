"""Quick script to verify whitelabel tables exist in production"""

import os

from sqlalchemy import create_engine, text

# Use production DATABASE_URL from environment
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ DATABASE_URL not set")
    exit(1)

try:
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if whitelabel tables exist
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name LIKE 'whitelabel_custom%'
            ORDER BY table_name
        """
            )
        )

        tables = [row[0] for row in result]

        if len(tables) == 3:
            print("✅ All whitelabel tables exist:")
            for table in tables:
                print(f"   - {table}")
        else:
            print(f"⚠️  Expected 3 tables, found {len(tables)}:")
            for table in tables:
                print(f"   - {table}")

except Exception as e:
    print(f"❌ Error: {e}")
