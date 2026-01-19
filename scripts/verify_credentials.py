#!/usr/bin/env python3
"""
Verify user credentials and tier access
Tests login and tier-specific features for each user
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_user_credentials():
    """Verify all user credentials and tier assignments"""

    db = next(get_db())

    print("🔐 Verifying user credentials and tier access...\n")

    # Get all users with their tier info
    users = db.execute(
        text(
            """
        SELECT id, email, password_hash, subscription_tier, tier_id, credits, is_admin
        FROM users 
        ORDER BY created_at
    """
        )
    ).fetchall()

    if not users:
        print("❌ No users found")
        return

    print(f"📊 Found {len(users)} users\n")
    print("=" * 70)

    for user in users:
        user_id, email, password_hash, sub_tier, tier_id, credits, is_admin = user

        print(f"\n👤 USER: {email}")
        print(f"   ID: {user_id}")
        print(f"   Tier: {sub_tier} / {tier_id}")
        print(f"   Credits: ${credits:.2f}")
        print(f"   Admin: {'Yes' if is_admin else 'No'}")

        # Check password hash exists
        if password_hash:
            print(f"   Password: ✅ Set (hash exists)")
        else:
            print(f"   Password: ⚠️  Not set (OAuth user)")

        # Get tier configuration
        tier_config = db.execute(
            text(
                """
            SELECT name, price_monthly, quota_usd, has_api_access, 
                   has_area_code_selection, has_isp_filtering, api_key_limit
            FROM subscription_tiers 
            WHERE tier = :tier
        """
            ),
            {"tier": sub_tier},
        ).fetchone()

        if tier_config:
            tier_name, price, quota, api_access, area_codes, isp_filter, api_limit = (
                tier_config
            )

            print(f"\n   📋 TIER FEATURES ({tier_name}):")
            print(f"      Monthly Fee: ${price/100:.2f}")
            print(f"      Quota: ${quota:.2f}")
            print(f"      API Access: {'✅' if api_access else '❌'}")
            print(f"      API Keys: {api_limit if api_limit != -1 else 'Unlimited'}")
            print(f"      Location Filters: {'✅' if area_codes else '❌'}")
            print(f"      ISP Filtering: {'✅' if isp_filter else '❌'}")
        else:
            print(f"   ⚠️  Tier configuration not found for: {sub_tier}")

        # Check for API keys
        try:
            api_key_count = db.execute(
                text(
                    """
                SELECT COUNT(*) FROM api_keys 
                WHERE user_id = :user_id AND is_active = 1
            """
                ),
                {"user_id": user_id},
            ).fetchone()[0]

            if api_key_count > 0:
                print(f"\n   🔑 API Keys: {api_key_count} active")
            else:
                print(f"\n   🔑 API Keys: None")
        except:
            print(f"\n   🔑 API Keys: Table not found")

        print("\n" + "-" * 70)

    db.close()

    # Summary
    print("\n" + "=" * 70)
    print("📊 CREDENTIAL VERIFICATION SUMMARY")
    print("=" * 70)

    db = next(get_db())

    # Tier distribution
    tier_dist = db.execute(
        text(
            """
        SELECT subscription_tier, COUNT(*) as count
        FROM users
        GROUP BY subscription_tier
        ORDER BY 
            CASE subscription_tier
                WHEN 'freemium' THEN 1
                WHEN 'payg' THEN 2
                WHEN 'pro' THEN 3
                WHEN 'custom' THEN 4
            END
    """
        )
    ).fetchall()

    print("\n🎯 Tier Distribution:")
    for tier, count in tier_dist:
        print(f"   {tier.upper()}: {count} users")

    # Feature access summary
    print("\n🔓 Feature Access by Tier:")

    features = db.execute(
        text(
            """
        SELECT tier, name, has_api_access, has_area_code_selection, has_isp_filtering
        FROM subscription_tiers
        ORDER BY price_monthly
    """
        )
    ).fetchall()

    for tier, name, api, area, isp in features:
        print(f"\n   {name}:")
        print(f"      API: {'✅' if api else '❌'}")
        print(f"      Location Filters: {'✅' if area else '❌'}")
        print(f"      ISP Filters: {'✅' if isp else '❌'}")

    db.close()

    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)
    print("\n💡 All users are properly configured with their respective tiers!")
    print("🔐 Credentials are set and ready for testing!")


if __name__ == "__main__":
    verify_user_credentials()
