#!/usr/bin/env python3
"""Migrate data from Render PostgreSQL backup to Neon."""

import csv
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Neon connection string
NEON_URL = "postgresql://neondb_owner:npg_ipg1faPdmEr6@ep-shy-king-ansjlp5g-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

BACKUP_DIR = Path("render_backup_final")

# Tables to migrate in order (respecting foreign keys)
TABLES = [
    "users",
    "subscription_tiers",
    "tiers",
    "pricing_templates",  # Must come before tier_pricing
    "tier_pricing",
    "sms_transactions",
    "verifications",
    "payment_logs",
    "notifications",
    "notification_settings",
    "activity_logs",
    "monthly_quota_usage",
]

# Column name mappings (CSV -> Database)
COLUMN_MAPPINGS = {"pricing_templates": {"metadata": "template_metadata"}}


def migrate_table(conn, table_name):
    """Migrate a single table from CSV to Neon."""
    csv_file = BACKUP_DIR / f"{table_name}.csv"

    if not csv_file.exists():
        print(f"⚠️  Skipping {table_name} - CSV not found")
        return 0

    print(f"📦 Migrating {table_name}...")

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            print(f"   ℹ️  {table_name} is empty")
            return 0

        # Get column names from CSV
        columns = list(rows[0].keys())

        # Apply column name mappings if needed
        if table_name in COLUMN_MAPPINGS:
            mapping = COLUMN_MAPPINGS[table_name]
            columns = [mapping.get(col, col) for col in columns]
            # Update rows with new column names
            new_rows = []
            for row in rows:
                new_row = {}
                for old_col, val in row.items():
                    new_col = mapping.get(old_col, old_col)
                    new_row[new_col] = val
                new_rows.append(new_row)
            rows = new_rows

        # Convert empty strings to None for proper NULL handling
        cleaned_rows = []
        for row in rows:
            cleaned_row = {}
            for col, val in row.items():
                if val == "":
                    cleaned_row[col] = None
                elif val == "t":
                    cleaned_row[col] = True
                elif val == "f":
                    cleaned_row[col] = False
                else:
                    cleaned_row[col] = val
            cleaned_rows.append(cleaned_row)

        # Build INSERT query
        cols_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        # Execute batch insert
        with conn.cursor() as cur:
            values = [[row[col] for col in columns] for row in cleaned_rows]
            for value_set in values:
                try:
                    cur.execute(query, value_set)
                except Exception as e:
                    print(f"   ⚠️  Error inserting row: {e}")
                    continue

        conn.commit()
        print(f"   ✅ Migrated {len(cleaned_rows)} rows")
        return len(cleaned_rows)


def main():
    """Main migration function."""
    print("🚀 Starting migration from Render to Neon...")
    print(f"📂 Backup directory: {BACKUP_DIR}")

    try:
        # Connect to Neon
        print("\n🔌 Connecting to Neon...")
        conn = psycopg2.connect(NEON_URL)
        print("✅ Connected to Neon PostgreSQL")

        total_rows = 0

        # Migrate each table
        for table in TABLES:
            try:
                rows = migrate_table(conn, table)
                total_rows += rows
            except Exception as e:
                print(f"❌ Error migrating {table}: {e}")
                continue

        print(f"\n✅ Migration complete! Total rows migrated: {total_rows}")

        # Close connection
        conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
