#!/usr/bin/env python3
"""Create reseller program tables."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_reseller_tables():
    """Create reseller program tables."""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Create reseller_accounts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reseller_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tier VARCHAR(50) DEFAULT 'bronze',
                volume_discount FLOAT DEFAULT 0.0,
                custom_rates JSON,
                credit_limit FLOAT DEFAULT 0.0,
                auto_topup_enabled BOOLEAN DEFAULT 0,
                auto_topup_threshold FLOAT DEFAULT 100.0,
                auto_topup_amount FLOAT DEFAULT 500.0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))
        
        # Create sub_accounts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sub_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                credits FLOAT DEFAULT 0.0,
                usage_limit FLOAT,
                rate_multiplier FLOAT DEFAULT 1.0,
                features JSON,
                is_active BOOLEAN DEFAULT 1,
                last_activity DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES reseller_accounts (id)
            )
        """))
        
        # Create sub_account_transactions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sub_account_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sub_account_id INTEGER NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL,
                description VARCHAR(255) NOT NULL,
                reference VARCHAR(100),
                balance_after FLOAT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sub_account_id) REFERENCES sub_accounts (id)
            )
        """))
        
        # Create credit_allocations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS credit_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                sub_account_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                allocation_type VARCHAR(50) DEFAULT 'manual',
                notes VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES reseller_accounts (id),
                FOREIGN KEY (sub_account_id) REFERENCES sub_accounts (id)
            )
        """))
        
        # Create bulk_operations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bulk_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                total_accounts INTEGER NOT NULL,
                processed_accounts INTEGER DEFAULT 0,
                failed_accounts INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'pending',
                operation_data JSON,
                error_log JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reseller_id) REFERENCES reseller_accounts (id)
            )
        """))
        
        # Add reseller relationship to users table if not exists
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN reseller_account_id INTEGER"))
        except:
            pass
        
        conn.commit()
        print("✅ Reseller program tables created successfully!")
        print("🏢 Reseller Tiers Available:")
        print("- Bronze: 5% discount, N1K credit limit")
        print("- Silver: 10% discount, N5K credit limit")
        print("- Gold: 20% discount, N25K credit limit")
        print("- Platinum: 35% discount, N100K credit limit")

if __name__ == "__main__":
    create_reseller_tables()