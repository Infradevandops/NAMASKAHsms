#!/usr/bin/env python3
"""Fix affiliate_commissions table schema."""

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Drop the problematic table
    conn.execute(text("DROP TABLE IF EXISTS affiliate_commissions CASCADE"))
    conn.commit()
    print("✅ Dropped affiliate_commissions table")

print("✅ Schema fixed. Restart the app to recreate tables.")
