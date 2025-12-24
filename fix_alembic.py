#!/usr/bin/env python3
"""Fix corrupted alembic_version table."""
import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

engine = create_engine(database_url)

with engine.connect() as conn:
    # Rollback any failed transaction
    conn.execute(text("ROLLBACK"))
    conn.commit()
    
    # Fix alembic_version
    conn.execute(text("DELETE FROM alembic_version"))
    conn.execute(text("INSERT INTO alembic_version VALUES ('cb2a98627849')"))
    conn.commit()
    
print("✅ Fixed alembic_version table")
