#!/usr/bin/env python3
"""Update SMS pricing to 3500 NGN equivalent ($2.12 at 1650 rate)."""

import os
import sys

from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    print(
        "Usage: DATABASE_URL='postgresql://...' python scripts/update_sms_pricing_3500ngn.py"
    )
    sys.exit(1)

print("🔧 Connecting to database...")
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        print("✅ Connected to database")

        # Update tier pricing
        print("\n📝 Updating SMS pricing to 3500 NGN ($2.12 USD)...")

        updates = [
            {"tier": "freemium", "overage_rate": 2.12},
            {"tier": "payg", "overage_rate": 2.12},
            {"tier": "pro", "overage_rate": 0.30},  # Keep overage rates
            {"tier": "custom", "overage_rate": 0.20},
        ]

        for update in updates:
            conn.execute(
                text(
                    """
                    UPDATE subscription_tiers
                    SET overage_rate = :overage_rate,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tier = :tier
                """
                ),
                update,
            )
            print(f"   ✅ Updated {update['tier']}: ${update['overage_rate']}/SMS")

        conn.commit()

        # Verify
        print("\n🔍 Verifying updated pricing...")
        result = conn.execute(
            text(
                """
                SELECT tier, name, overage_rate
                FROM subscription_tiers
                ORDER BY price_monthly
            """
            )
        )
        tiers = result.fetchall()

        print(f"\n✅ Current SMS pricing:")
        for tier in tiers:
            ngn_price = tier[2] * 1650  # Convert to NGN
            print(f"   - {tier[1]}: ${tier[2]:.2f} (₦{ngn_price:.0f})")

        print("\n🎉 SMS pricing updated successfully!")
        print("\n💡 Note: Freemium & PAYG now cost ₦3,500 per SMS")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
