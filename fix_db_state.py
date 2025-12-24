#!/usr/bin/env python3
"""Fix PostgreSQL alembic_version table - Production safe."""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to PostgreSQL database...")

try:
    # Use psycopg2 directly for better transaction control
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Terminate any existing connections to clear failed transactions
    cur.execute("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = current_database() 
        AND pid <> pg_backend_pid()
        AND state = 'idle in transaction (aborted)'
    """)
    
    # Check current state
    cur.execute("SELECT version_num FROM alembic_version")
    result = cur.fetchone()
    print(f"Current alembic version: {result[0] if result else 'None'}")
    
    # Fix the version
    cur.execute("DELETE FROM alembic_version")
    cur.execute("INSERT INTO alembic_version VALUES ('cb2a98627849')")
    
    cur.close()
    conn.close()
    
    print("✅ Fixed alembic_version to: cb2a98627849")
    print("✅ Database ready for deployment")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
