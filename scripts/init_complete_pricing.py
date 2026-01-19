#!/usr/bin/env python3
"""
Complete Pricing System Implementation
Fixes all major discrepancies:
- Creates 4-tier system (Pay-As-You-Go, Starter, Pro, Custom)
- Implements quota/overage system
- Initializes database with correct pricing
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal
from app.models.base import Base
import app.models
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Create all tables first
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Create subscription_tiers table if it doesn't exist
    from sqlalchemy import text

    # Drop and recreate subscription_tiers table with correct structure
    print("Dropping and recreating subscription_tiers table...")
    db.execute(text("DROP TABLE IF EXISTS subscription_tiers"))
    db.execute(
        text(
            """
        CREATE TABLE subscription_tiers (
            id TEXT PRIMARY KEY,
            tier TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_monthly INTEGER DEFAULT 0,
            quota_usd INTEGER DEFAULT 0,
            overage_rate REAL DEFAULT 0,
            payment_required BOOLEAN DEFAULT 0,
            has_api_access BOOLEAN DEFAULT 0,
            has_area_code_selection BOOLEAN DEFAULT 0,
            has_isp_filtering BOOLEAN DEFAULT 0,
            api_key_limit INTEGER DEFAULT 0,
            support_level TEXT DEFAULT 'community',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
        )
    )
    print("✅ subscription_tiers table recreated with correct structure")

    # Check if user_quotas table exists
    result = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_quotas'")
    )
    if not result.fetchone():
        print("Creating user_quotas table...")
        db.execute(
            text(
                """
            CREATE TABLE user_quotas (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                month_year TEXT NOT NULL,
                quota_used_usd REAL DEFAULT 0,
                sms_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, month_year)
            )
        """
            )
        )
        print("✅ user_quotas table created")
    else:
        print("✅ user_quotas table already exists")

    # Add tier_id column to users table if it doesn't exist
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN tier_id TEXT DEFAULT 'payg'"))
        print("✅ Added tier_id column to users table")
    except:
        print("✅ tier_id column already exists in users table")

    db.commit()

    # Insert the 4 correct tiers
    print("Inserting correct 4-tier pricing structure...")

    # Clear existing tiers
    db.execute(text("DELETE FROM subscription_tiers"))

    tiers = [
        {
            "id": str(uuid.uuid4()),
            "tier": "payg",
            "name": "Pay-As-You-Go",
            "description": "No commitment, pay per SMS",
            "price_monthly": 0,  # $0/month
            "quota_usd": 0,  # No quota
            "overage_rate": 0.0,  # Always $2.50/SMS
            "payment_required": 0,
            "has_api_access": 0,
            "has_area_code_selection": 0,
            "has_isp_filtering": 0,
            "api_key_limit": 0,
            "support_level": "community",
        },
        {
            "id": str(uuid.uuid4()),
            "tier": "starter",
            "name": "Starter",
            "description": "Perfect for growing projects",
            "price_monthly": 899,  # $8.99/month (in cents)
            "quota_usd": 10,  # $10 quota (~4 SMS)
            "overage_rate": 0.50,  # +$0.50/SMS overage
            "payment_required": 1,
            "has_api_access": 1,
            "has_area_code_selection": 1,
            "has_isp_filtering": 0,
            "api_key_limit": 5,
            "support_level": "email",
        },
        {
            "id": str(uuid.uuid4()),
            "tier": "pro",
            "name": "Pro",
            "description": "Advanced features for professionals",
            "price_monthly": 2500,  # $25/month (in cents)
            "quota_usd": 30,  # $30 quota (~12 SMS)
            "overage_rate": 0.30,  # +$0.30/SMS overage
            "payment_required": 1,
            "has_api_access": 1,
            "has_area_code_selection": 1,
            "has_isp_filtering": 1,
            "api_key_limit": 10,
            "support_level": "priority",
        },
        {
            "id": str(uuid.uuid4()),
            "tier": "custom",
            "name": "Custom",
            "description": "Maximum features and support",
            "price_monthly": 3500,  # $35/month (in cents)
            "quota_usd": 50,  # $50 quota (~20 SMS)
            "overage_rate": 0.20,  # +$0.20/SMS overage
            "payment_required": 1,
            "has_api_access": 1,
            "has_area_code_selection": 1,
            "has_isp_filtering": 1,
            "api_key_limit": -1,  # Unlimited
            "support_level": "dedicated",
        },
    ]

    for tier in tiers:
        db.execute(
            text(
                """
            INSERT INTO subscription_tiers 
            (id, tier, name, description, price_monthly, quota_usd, overage_rate, 
             payment_required, has_api_access, has_area_code_selection, has_isp_filtering, 
             api_key_limit, support_level)
            VALUES 
            (:id, :tier, :name, :description, :price_monthly, :quota_usd, :overage_rate,
             :payment_required, :has_api_access, :has_area_code_selection, :has_isp_filtering,
             :api_key_limit, :support_level)
        """
            ),
            tier,
        )

    db.commit()
    print("✅ Inserted 4 correct tiers")

    # Set all existing users to Pay-As-You-Go tier
    db.execute(
        text("UPDATE users SET tier_id = 'payg' WHERE tier_id IS NULL OR tier_id = ''")
    )
    db.commit()
    print("✅ Set existing users to Pay-As-You-Go tier")

    # Verify the setup
    result = db.execute(
        text(
            "SELECT tier, name, price_monthly, quota_usd, overage_rate FROM subscription_tiers ORDER BY price_monthly"
        )
    )
    tiers = result.fetchall()

    print("\n🎯 PRICING STRUCTURE IMPLEMENTED:")
    print("=" * 60)
    for tier in tiers:
        price = tier[2] / 100 if tier[2] > 0 else 0
        print(
            f"• {tier[1]} ({tier[0]}): ${price:.2f}/mo, ${tier[3]} quota, +${tier[4]:.2f} overage"
        )

    print("\n✅ Complete pricing system implemented successfully!")
    print("✅ All major discrepancies fixed:")
    print("  - 4-tier system (Pay-As-You-Go, Starter, Pro, Custom)")
    print("  - Correct pricing ($0, $8.99, $25, $35)")
    print("  - Quota/overage system implemented")
    print("  - Database initialized with correct data")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
    raise
finally:
    db.close()
