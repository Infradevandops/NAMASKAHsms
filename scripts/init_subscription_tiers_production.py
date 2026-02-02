#!/usr/bin/env python3
"""Initialize subscription_tiers table in production database."""


# Get database URL from environment

import os
import sys
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    print(
        "Usage: DATABASE_URL='postgresql://...' python scripts/init_subscription_tiers_production.py"
    )
    sys.exit(1)

print("🔧 Connecting to database...")
engine = create_engine(database_url)

try:
with engine.connect() as conn:
        print("✅ Connected to database")

        # Create subscription_tiers table
        print("\n📋 Creating subscription_tiers table...")
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS subscription_tiers (
                id TEXT PRIMARY KEY,
                tier TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price_monthly INTEGER NOT NULL,
                quota_usd DECIMAL(10, 2) NOT NULL,
                overage_rate DECIMAL(10, 2) NOT NULL,
                has_api_access BOOLEAN DEFAULT FALSE,
                has_area_code_selection BOOLEAN DEFAULT FALSE,
                has_isp_filtering BOOLEAN DEFAULT FALSE,
                api_key_limit INTEGER DEFAULT 0,
                support_level TEXT DEFAULT 'community',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )
        conn.commit()
        print("✅ Table created")

        # Insert tier data
        print("\n📝 Inserting tier definitions...")

        tiers = [
            {
                "id": "tier_freemium",
                "tier": "freemium",
                "name": "Freemium",
                "price_monthly": 0,
                "quota_usd": 0,
                "overage_rate": 2.22,
                "has_api_access": False,
                "has_area_code_selection": False,
                "has_isp_filtering": False,
                "api_key_limit": 0,
                "support_level": "community",
            },
            {
                "id": "tier_payg",
                "tier": "payg",
                "name": "Pay-As-You-Go",
                "price_monthly": 0,
                "quota_usd": 0,
                "overage_rate": 2.50,
                "has_api_access": True,
                "has_area_code_selection": True,
                "has_isp_filtering": False,
                "api_key_limit": 5,
                "support_level": "community",
            },
            {
                "id": "tier_pro",
                "tier": "pro",
                "name": "Pro",
                "price_monthly": 2500,  # $25.00
                "quota_usd": 30.00,
                "overage_rate": 2.20,
                "has_api_access": True,
                "has_area_code_selection": True,
                "has_isp_filtering": True,
                "api_key_limit": 10,
                "support_level": "priority",
            },
            {
                "id": "tier_custom",
                "tier": "custom",
                "name": "Custom",
                "price_monthly": 3500,  # $35.00
                "quota_usd": 50.00,
                "overage_rate": 2.10,
                "has_api_access": True,
                "has_area_code_selection": True,
                "has_isp_filtering": True,
                "api_key_limit": -1,  # Unlimited
                "support_level": "dedicated",
            },
        ]

for tier in tiers:
            conn.execute(
                text(
                    """
                INSERT INTO subscription_tiers
                (id, tier, name, price_monthly, quota_usd, overage_rate,
                 has_api_access, has_area_code_selection, has_isp_filtering,
                 api_key_limit, support_level)
                VALUES
                (:id, :tier, :name, :price_monthly, :quota_usd, :overage_rate,
                 :has_api_access, :has_area_code_selection, :has_isp_filtering,
                 :api_key_limit, :support_level)
                ON CONFLICT (tier) DO UPDATE SET
                    name = EXCLUDED.name,
                    price_monthly = EXCLUDED.price_monthly,
                    quota_usd = EXCLUDED.quota_usd,
                    overage_rate = EXCLUDED.overage_rate,
                    has_api_access = EXCLUDED.has_api_access,
                    has_area_code_selection = EXCLUDED.has_area_code_selection,
                    has_isp_filtering = EXCLUDED.has_isp_filtering,
                    api_key_limit = EXCLUDED.api_key_limit,
                    support_level = EXCLUDED.support_level,
                    updated_at = CURRENT_TIMESTAMP;
            """
                ),
                tier,
            )
            print(f"   ✅ {tier['name']} tier")

        conn.commit()

        # Verify
        print("\n🔍 Verifying tiers...")
        result = conn.execute(
            text(
                "SELECT tier, name, price_monthly FROM subscription_tiers ORDER BY price_monthly;"
            )
        )
        tiers = result.fetchall()

        print(f"\n✅ Found {len(tiers)} tiers:")
for tier in tiers:
            price = tier[2] / 100 if tier[2] > 0 else 0
            print(f"   - {tier[1]}: ${price:.2f}/mo")

        print("\n🎉 Subscription tiers initialized successfully!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)