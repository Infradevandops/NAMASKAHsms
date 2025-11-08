#!/usr/bin/env python3
"""Create commission and revenue sharing tables."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_commission_tables():
    """Create commission tables directly."""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Create commission_tiers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS commission_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                base_rate FLOAT NOT NULL,
                bonus_rate FLOAT DEFAULT 0.0,
                min_volume FLOAT DEFAULT 0.0,
                min_referrals INTEGER DEFAULT 0,
                requirements JSON,
                benefits JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create revenue_shares table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS revenue_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                transaction_id VARCHAR(255) NOT NULL,
                revenue_amount FLOAT NOT NULL,
                commission_rate FLOAT NOT NULL,
                commission_amount FLOAT NOT NULL,
                tier_name VARCHAR(50) NOT NULL,
                attribution_type VARCHAR(50) DEFAULT 'last_touch',
                status VARCHAR(50) DEFAULT 'pending',
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES users (id)
            )
        """))
        
        # Create payout_requests table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payout_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                currency VARCHAR(3) DEFAULT 'NGN',
                payment_method VARCHAR(50) NOT NULL,
                payment_details JSON,
                status VARCHAR(50) DEFAULT 'pending',
                processed_at DATETIME,
                transaction_reference VARCHAR(255),
                admin_notes VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES users (id)
            )
        """))
        
        # Insert commission tiers
        conn.execute(text("""
            INSERT OR IGNORE INTO commission_tiers 
            (name, base_rate, bonus_rate, min_volume, min_referrals, benefits, is_active)
            VALUES 
            ('starter', 0.05, 0.02, 0, 0, 
             '{"support": "email", "materials": "basic", "payouts": "monthly"}', 1),
            ('professional', 0.15, 0.05, 1000, 5,
             '{"support": "priority", "materials": "advanced", "payouts": "bi-weekly", "analytics": true}', 1),
            ('enterprise', 0.25, 0.10, 10000, 25,
             '{"support": "dedicated", "materials": "premium", "payouts": "weekly", "analytics": true, "custom_rates": true}', 1),
            ('whitelabel', 0.40, 0.15, 50000, 100,
             '{"support": "dedicated", "materials": "premium", "payouts": "weekly", "analytics": true, "custom_rates": true, "whitelabel": true}', 1)
        """))
        
        conn.commit()
        print("✅ Commission tables created successfully!")
        print("📊 Commission Tiers:")
        print("- Starter: 5% + 2% bonus")
        print("- Professional: 15% + 5% bonus") 
        print("- Enterprise: 25% + 10% bonus")
        print("- White-label: 40% + 15% bonus")

if __name__ == "__main__":
    create_commission_tables()