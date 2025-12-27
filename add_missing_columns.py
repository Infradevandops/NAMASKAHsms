#!/usr/bin/env python3
"""Add missing columns to users table."""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./namaskah.db")

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

print("Adding missing columns to users table...")

with engine.connect() as conn:
    # Add language column if missing
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'"))
        conn.commit()
        print("✅ Added language column")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e).lower():
            print("⚠️  language column already exists")
        else:
            print(f"❌ Error adding language: {e}")
    
    # Add currency column if missing
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN currency VARCHAR(10) DEFAULT 'USD'"))
        conn.commit()
        print("✅ Added currency column")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e).lower():
            print("⚠️  currency column already exists")
        else:
            print(f"❌ Error adding currency: {e}")

print("\n✅ Migration complete!")
