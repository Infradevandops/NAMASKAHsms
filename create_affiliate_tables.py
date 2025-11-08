#!/usr/bin/env python3
"""Create affiliate tables directly."""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

from app.core.config import settings


def create_affiliate_tables():
    """Create affiliate tables directly."""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Create affiliate_programs table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS affiliate_programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                program_type VARCHAR(50) NOT NULL,
                commission_rate FLOAT NOT NULL,
                tier_requirements JSON,
                features JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Create affiliate_applications table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS affiliate_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) NOT NULL,
                program_type VARCHAR(50) NOT NULL,
                program_options JSON,
                message TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                admin_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Create affiliate_commissions table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS affiliate_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliate_id INTEGER NOT NULL,
                transaction_id VARCHAR(255) NOT NULL,
                amount FLOAT NOT NULL,
                commission_rate FLOAT NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                payout_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES users (id)
            )
        """
            )
        )

        # Add affiliate fields to users table if they don't exist
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN affiliate_id VARCHAR(50)"))
        except:
            pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN partner_type VARCHAR(50)"))
        except:
            pass

        try:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN commission_tier VARCHAR(50)")
            )
        except:
            pass

        try:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN is_affiliate BOOLEAN DEFAULT 0")
            )
        except:
            pass

        # Insert default affiliate programs
        conn.execute(
            text(
                """
            INSERT OR IGNORE INTO affiliate_programs 
            (name, program_type, commission_rate, tier_requirements, features, is_active)
            VALUES 
            ('Individual Referral Program', 'referral', 0.10, 
             '{"min_referrals": 0, "min_revenue": 0}',
             '{"sms_verification": true, "whatsapp_integration": true, "payment_processing": true, "api_access": true}',
             1),
            ('Enterprise Affiliate Program', 'enterprise', 0.25,
             '{"min_monthly_revenue": 1000, "min_referrals": 10}',
             '{"white_label_solutions": true, "reseller_programs": true, "custom_integration_support": true, "dedicated_account_manager": true}',
             1)
        """
            )
        )

        conn.commit()
        print("✅ Affiliate tables created successfully!")


if __name__ == "__main__":
    create_affiliate_tables()
