#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

def create_tables():
    db_url = os.getenv('DATABASE_URL', 'sqlite:///namaskah_dev.db')
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sms_messages (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                rental_id TEXT,
                from_number TEXT,
                text TEXT,
                external_id TEXT,
                received_at TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
    
    print("Tables created successfully")

if __name__ == '__main__':
    create_tables()
