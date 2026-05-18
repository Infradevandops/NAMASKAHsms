#!/usr/bin/env python3
"""
import os
import sys
from app.core.database import get_db
from app.models.subscription_tier import SubscriptionTier, TierEnum

Initialize New Freemium Tier Structure
Creates the 4-tier freemium model: Freemium, Pay-As-You-Go, Pro, Custom
"""


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_freemium_tiers():

    """Create the new 4-tier freemium structure"""

    db = next(get_db())

    # Clear existing tiers
    db.query(SubscriptionTier).delete()

    tiers_data = [
        {
            "tier": TierEnum.FREEMIUM,
            "name": "Freemium",
            "description": "Perfect for trying out our service - 9 SMS per $20 deposit",
            "price_monthly": 0,
            "payment_required": False,
            "quota_usd": 0.0,
            "overage_rate": 2.22,  # Effective rate for freemium
            "has_api_access": False,
            "has_area_code_selection": False,
            "has_isp_filtering": False,
            "api_key_limit": 0,
            "daily_verification_limit": 1000,
            "monthly_verification_limit": 30000,
            "country_limit": -1,
            "sms_retention_days": 7,
            "support_level": "community",
            "features": {
                "deposit_bonus": True,
                "sms_per_deposit": 9,
                "deposit_amount": 20.0,
                "effective_rate": 2.22,
                "random_numbers_only": True,
            },
        },
        {
            "tier": TierEnum.PAYG,
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
            "features": {
                "base_rate": 2.50,
                "state_filter_cost": 0.25,
                "isp_filter_cost": 0.50,
                "combined_filter_cost": 0.75,
                "custom_balance": True,
                "no_monthly_commitment": True,
            },
        },
        {
            "tier": TierEnum.PRO,
            "name": "Pro",
            "description": "For businesses and developers - API access with all filters included",
            "price_monthly": 2500,  # $25.00 in cents
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
            "features": {
                "included_quota": 15.0,
                "overage_rate": 0.30,
                "all_filters_included": True,
                "affiliate_program": True,
                "priority_support": True,
                "api_keys": 10,
            },
        },
        {
            "tier": TierEnum.CUSTOM,
            "name": "Custom",
            "description": "Enterprise tier with unlimited API keys and enhanced affiliate program",
            "price_monthly": 3500,  # $35.00 in cents
            "payment_required": True,
            "quota_usd": 25.0,
            "overage_rate": 0.20,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": -1,  # Unlimited
            "daily_verification_limit": 100000,
            "monthly_verification_limit": 3000000,
            "country_limit": -1,
            "sms_retention_days": 90,
            "support_level": "dedicated",
            "features": {
                "included_quota": 25.0,
                "overage_rate": 0.20,
                "unlimited_api_keys": True,
                "enhanced_affiliate_program": True,
                "dedicated_support": True,
                "priority_features": True,
                "white_label_options": True,
            },
        },
    ]

    created_count = 0

for tier_data in tiers_data:
        tier = SubscriptionTier(**tier_data)
        db.add(tier)
        created_count += 1
        print(f"✅ Created tier: {tier_data['name']}")

    db.commit()
    db.close()

    print(f"\n🎉 Successfully created {created_count} subscription tiers!")
    print("\n📋 New tier structure:")
    print("   • Freemium ($0/mo) - 9 SMS per $20 deposit")
    print("   • Pay-As-You-Go ($0/mo) - $2.50/SMS + filters")
    print("   • Pro ($25/mo) - $15 quota + API access")
    print("   • Custom ($35/mo) - $25 quota + unlimited API")
    print("\n🚀 New users will automatically start in Freemium tier!")


if __name__ == "__main__":
    print("🏗️  Initializing New Freemium Tier Structure...")
    create_freemium_tiers()
