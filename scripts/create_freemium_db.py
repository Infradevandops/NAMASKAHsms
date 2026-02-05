#!/usr/bin/env python3
"""
import os
import sys
from sqlalchemy import text
from app.core.database import get_db

Create subscription_tiers table and populate with freemium structure
"""


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_subscription_tiers_table():

    """Create subscription_tiers table and populate with new structure"""

    db = next(get_db())

    # Create the table
    db.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS subscription_tiers (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tier TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_monthly INTEGER DEFAULT 0 NOT NULL,
            payment_required BOOLEAN DEFAULT FALSE NOT NULL,
            quota_usd REAL DEFAULT 0.0,
            overage_rate REAL DEFAULT 0.0,
            has_api_access BOOLEAN DEFAULT FALSE NOT NULL,
            has_area_code_selection BOOLEAN DEFAULT FALSE NOT NULL,
            has_isp_filtering BOOLEAN DEFAULT FALSE NOT NULL,
            api_key_limit INTEGER DEFAULT 0 NOT NULL,
            daily_verification_limit INTEGER DEFAULT 100 NOT NULL,
            monthly_verification_limit INTEGER DEFAULT 3000 NOT NULL,
            country_limit INTEGER DEFAULT 5 NOT NULL,
            sms_retention_days INTEGER DEFAULT 1 NOT NULL,
            support_level TEXT DEFAULT 'community',
            features TEXT DEFAULT '{}',
            rate_limit_per_minute INTEGER DEFAULT 10 NOT NULL,
            rate_limit_per_hour INTEGER DEFAULT 100 NOT NULL
        )
    """
        )
    )

    # Clear existing data
    db.execute(text("DELETE FROM subscription_tiers"))

    # Insert new tier structure
    tiers_data = [
        {
            "id": "freemium_tier",
            "tier": "freemium",
            "name": "Freemium",
            "description": "Perfect for trying out our service - 9 SMS per $20 deposit",
            "price_monthly": 0,
            "payment_required": False,
            "quota_usd": 0.0,
            "overage_rate": 2.22,
            "has_api_access": False,
            "has_area_code_selection": False,
            "has_isp_filtering": False,
            "api_key_limit": 0,
            "daily_verification_limit": 1000,
            "monthly_verification_limit": 30000,
            "country_limit": -1,
            "sms_retention_days": 7,
            "support_level": "community",
            "features": '{"deposit_bonus": true, "sms_per_deposit": 9, "deposit_amount": 20.0, "effective_rate": 2.22, "random_numbers_only": true}',
        },
        {
            "id": "payg_tier",
            "tier": "payg",
            "name": "Pay-As-You-Go",
            "description": "Flexible pricing with location and ISP filtering options",
            "price_monthly": 0,
            "payment_required": False,
            "quota_usd": 0.0,
            "overage_rate": 2.50,
            "has_api_access": False,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": 0,
            "daily_verification_limit": 10000,
            "monthly_verification_limit": 300000,
            "country_limit": -1,
            "sms_retention_days": 14,
            "support_level": "community",
            "features": '{"base_rate": 2.50, "state_filter_cost": 0.25, "isp_filter_cost": 0.50, "combined_filter_cost": 0.75, "custom_balance": true, "no_monthly_commitment": true}',
        },
        {
            "id": "pro_tier",
            "tier": "pro",
            "name": "Pro",
            "description": "For businesses and developers - API access with all filters included",
            "price_monthly": 2500,
            "payment_required": True,
            "quota_usd": 15.0,
            "overage_rate": 0.30,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": 10,
            "daily_verification_limit": 50000,
            "monthly_verification_limit": 1500000,
            "country_limit": -1,
            "sms_retention_days": 30,
            "support_level": "priority",
            "features": '{"included_quota": 15.0, "overage_rate": 0.30, "all_filters_included": true, "affiliate_program": true, "priority_support": true, "api_keys": 10}',
        },
        {
            "id": "custom_tier",
            "tier": "custom",
            "name": "Custom",
            "description": "Enterprise tier with unlimited API keys and enhanced affiliate program",
            "price_monthly": 3500,
            "payment_required": True,
            "quota_usd": 25.0,
            "overage_rate": 0.20,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": -1,
            "daily_verification_limit": 100000,
            "monthly_verification_limit": 3000000,
            "country_limit": -1,
            "sms_retention_days": 90,
            "support_level": "dedicated",
            "features": '{"included_quota": 25.0, "overage_rate": 0.20, "unlimited_api_keys": true, "enhanced_affiliate_program": true, "dedicated_support": true, "priority_features": true, "white_label_options": true}',
        },
    ]

for tier_data in tiers_data:
        db.execute(
            text(
                """
            INSERT INTO subscription_tiers (
                id, tier, name, description, price_monthly, payment_required,
                quota_usd, overage_rate, has_api_access, has_area_code_selection,
                has_isp_filtering, api_key_limit, daily_verification_limit,
                monthly_verification_limit, country_limit, sms_retention_days,
                support_level, features, rate_limit_per_minute, rate_limit_per_hour
            ) VALUES (
                :id, :tier, :name, :description, :price_monthly, :payment_required,
                :quota_usd, :overage_rate, :has_api_access, :has_area_code_selection,
                :has_isp_filtering, :api_key_limit, :daily_verification_limit,
                :monthly_verification_limit, :country_limit, :sms_retention_days,
                :support_level, :features, :rate_limit_per_minute, :rate_limit_per_hour
            )
        """
            ),
            {**tier_data, "rate_limit_per_minute": 10, "rate_limit_per_hour": 100},
        )
        print(f"✅ Created tier: {tier_data['name']}")

    # Update existing users to freemium tier
    db.execute(
        text(
            """
        UPDATE users
        SET subscription_tier = 'freemium', tier_id = 'freemium'
        WHERE subscription_tier IS NULL OR subscription_tier = ''
    """
        )
    )

    db.commit()
    db.close()

    print(
        "\n🎉 Successfully created subscription_tiers table and populated with 4 tiers!"
    )
    print("\n📋 New tier structure:")
    print("   • Freemium ($0/mo) - 9 SMS per $20 deposit")
    print("   • Pay-As-You-Go ($0/mo) - $2.50/SMS + filters")
    print("   • Pro ($25/mo) - $15 quota + API access")
    print("   • Custom ($35/mo) - $25 quota + unlimited API")
    print("\n🚀 All users updated to start in Freemium tier!")


if __name__ == "__main__":
    print(
        "🏗️  Creating subscription_tiers table and populating with freemium structure..."
    )
    create_subscription_tiers_table()
