#!/usr/bin/env python3
"""
import os
import sys
from app.core.database import get_db
from app.models.pricing_template import PricingHistory, PricingTemplate, TierPricing
from app.models.user import User

Initialize Pricing Templates for Namaskah Admin Dashboard
Creates Standard, Promotional, and Holiday pricing templates
"""


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_pricing_templates():

    """Create the three main pricing templates"""

    db = next(get_db())

    # Get admin user
    admin_user = db.query(User).filter(User.is_admin).first()
if not admin_user:
        print("❌ No admin user found. Please create an admin user first.")
        return

    templates_data = [
        {
            "name": "Standard Pricing",
            "description": "Regular pricing for normal operations",
            "is_active": True,
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0.00,
                    "included_quota": 0.00,
                    "overage_rate": 2.50,
                    "features": ["Random US numbers", "100/day"],
                    "api_keys_limit": 0,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 8.99,
                    "included_quota": 10.00,
                    "overage_rate": 0.50,
                    "features": ["Area code filtering", "1,000/day", "5 API keys"],
                    "api_keys_limit": 5,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 25.00,
                    "included_quota": 30.00,
                    "overage_rate": 0.30,
                    "features": ["Area + ISP filtering", "10,000/day", "10 API keys"],
                    "api_keys_limit": 10,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 35.00,
                    "included_quota": 50.00,
                    "overage_rate": 0.20,
                    "features": ["All features", "Unlimited", "Unlimited API keys"],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
        {
            "name": "Promotional 50% O",
            "description": "Limited time promotional pricing - 50% off all plans",
            "is_active": False,
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0.00,
                    "included_quota": 0.00,
                    "overage_rate": 2.50,
                    "features": ["Random US numbers", "100/day"],
                    "api_keys_limit": 0,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 4.49,  # 50% off
                    "included_quota": 15.00,  # Bonus quota
                    "overage_rate": 0.40,
                    "features": [
                        "Area code filtering",
                        "1,500/day",
                        "5 API keys",
                        "🎉 50% OFF",
                    ],
                    "api_keys_limit": 5,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 12.50,  # 50% off
                    "included_quota": 40.00,  # Bonus quota
                    "overage_rate": 0.25,
                    "features": [
                        "Area + ISP filtering",
                        "15,000/day",
                        "15 API keys",
                        "🎉 50% OFF",
                    ],
                    "api_keys_limit": 15,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 17.50,  # 50% off
                    "included_quota": 70.00,  # Bonus quota
                    "overage_rate": 0.15,
                    "features": [
                        "All features",
                        "Unlimited",
                        "Unlimited API keys",
                        "🎉 50% OFF",
                    ],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
        {
            "name": "Holiday Special",
            "description": "Holiday season special pricing with bonus features",
            "is_active": False,
            "tiers": [
                {
                    "tier_name": "Freemium",
                    "monthly_price": 0.00,
                    "included_quota": 5.00,  # Holiday bonus
                    "overage_rate": 2.00,
                    "features": [
                        "Random US numbers",
                        "200/day",
                        "🎄 Holiday Bonus",
                        "1 API key",
                    ],
                    "api_keys_limit": 1,
                    "display_order": 1,
                },
                {
                    "tier_name": "Starter",
                    "monthly_price": 6.99,  # Holiday discount
                    "included_quota": 20.00,  # Double quota
                    "overage_rate": 0.35,
                    "features": [
                        "Area code filtering",
                        "2,000/day",
                        "8 API keys",
                        "🎄 Holiday Special",
                    ],
                    "api_keys_limit": 8,
                    "display_order": 2,
                },
                {
                    "tier_name": "Pro",
                    "monthly_price": 19.99,  # Holiday discount
                    "included_quota": 50.00,  # Bonus quota
                    "overage_rate": 0.20,
                    "features": [
                        "Area + ISP filtering",
                        "20,000/day",
                        "20 API keys",
                        "🎄 Holiday Special",
                    ],
                    "api_keys_limit": 20,
                    "display_order": 3,
                },
                {
                    "tier_name": "Custom",
                    "monthly_price": 29.99,  # Holiday discount
                    "included_quota": 100.00,  # Double quota
                    "overage_rate": 0.10,
                    "features": [
                        "All features",
                        "Unlimited",
                        "Unlimited API keys",
                        "🎄 Holiday Special",
                    ],
                    "api_keys_limit": -1,
                    "display_order": 4,
                },
            ],
        },
    ]

    created_count = 0

for template_data in templates_data:
        # Check if template already exists
        existing = (
            db.query(PricingTemplate)
            .filter(PricingTemplate.name == template_data["name"])
            .first()
        )
if existing:
            print(f"⚠️  Template '{template_data['name']}' already exists, skipping...")
            continue

        # Create template
        template = PricingTemplate(
            name=template_data["name"],
            description=template_data["description"],
            region="US",
            currency="USD",
            created_by=admin_user.id,
            is_active=template_data["is_active"],
        )
        db.add(template)
        db.flush()  # Get the ID

        # Create tiers
for tier_data in template_data["tiers"]:
            tier = TierPricing(
                template_id=template.id,
                tier_name=tier_data["tier_name"],
                monthly_price=tier_data["monthly_price"],
                included_quota=tier_data["included_quota"],
                overage_rate=tier_data["overage_rate"],
                features=tier_data["features"],
                api_keys_limit=tier_data["api_keys_limit"],
                display_order=tier_data["display_order"],
            )
            db.add(tier)

        # Log creation
        history = PricingHistory(
            template_id=template.id,
            action="created",
            changed_by=admin_user.id,
            notes=f"Template '{template.name}' created with {len(template_data['tiers'])} tiers",
        )
        db.add(history)

        created_count += 1
        print(f"✅ Created template: {template.name}")

    db.commit()
    db.close()

    print(f"\n🎉 Successfully created {created_count} pricing templates!")
    print("\n📋 Available templates:")
    print("   • Standard Pricing (Active)")
    print("   • Promotional 50% O")
    print("   • Holiday Special")
    print("\n🚀 Admin can now switch between templates at /admin")


if __name__ == "__main__":
    print("🏗️  Initializing Namaskah Pricing Templates...")
    create_pricing_templates()