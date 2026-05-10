#!/usr/bin/env python3
"""Setup test users for area code tier gating manual testing.

This script creates 4 test users (one for each tier) with sufficient credits
for testing the area code tier gating feature.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_test_users(db: Session):
    """Create test users for all 4 tiers."""

    print("=" * 60)
    print("Area Code Tier Gating - Test User Setup")
    print("=" * 60)

    # Test password for all users
    test_password = "test123"
    hashed_password = hash_password(test_password)

    test_users = [
        {
            "id": "test_freemium",
            "email": "freemium@test.com",
            "username": "test_freemium",
            "subscription_tier": "freemium",
            "credits": 50.0,
            "bonus_sms_balance": 5,
        },
        {
            "id": "test_payg",
            "email": "payg@test.com",
            "username": "test_payg",
            "subscription_tier": "payg",
            "credits": 50.0,
            "bonus_sms_balance": 0,
        },
        {
            "id": "test_pro",
            "email": "pro@test.com",
            "username": "test_pro",
            "subscription_tier": "pro",
            "credits": 50.0,
            "bonus_sms_balance": 0,
        },
        {
            "id": "test_custom",
            "email": "custom@test.com",
            "username": "test_custom",
            "subscription_tier": "custom",
            "credits": 50.0,
            "bonus_sms_balance": 0,
        },
    ]

    created_count = 0
    updated_count = 0

    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()

        if existing_user:
            # Update existing user
            existing_user.subscription_tier = user_data["subscription_tier"]
            existing_user.credits = user_data["credits"]
            existing_user.bonus_sms_balance = user_data.get("bonus_sms_balance", 0)
            existing_user.password_hash = hashed_password
            print(
                f"✅ Updated: {user_data['email']} ({user_data['subscription_tier']})"
            )
            updated_count += 1
        else:
            # Create new user
            new_user = User(
                id=user_data["id"],
                email=user_data["email"],
                username=user_data.get("username", user_data["email"].split("@")[0]),
                password_hash=hashed_password,
                subscription_tier=user_data["subscription_tier"],
                credits=user_data["credits"],
                bonus_sms_balance=user_data.get("bonus_sms_balance", 0),
                email_verified=True,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(new_user)
            print(
                f"✅ Created: {user_data['email']} ({user_data['subscription_tier']})"
            )
            created_count += 1

    db.commit()

    print("\n" + "=" * 60)
    print("Test User Setup Complete")
    print("=" * 60)
    print(f"Created: {created_count} users")
    print(f"Updated: {updated_count} users")
    print(f"Total: {created_count + updated_count} users ready for testing")

    print("\n📋 Test User Credentials:")
    print("-" * 60)
    for user_data in test_users:
        print(f"Email: {user_data['email']}")
        print(f"Password: {test_password}")
        print(f"Tier: {user_data['subscription_tier']}")
        print(f"Credits: ${user_data['credits']:.2f}")
        print("-" * 60)

    print("\n🧪 Next Steps:")
    print("1. Start the application: ./start.sh")
    print("2. Open: http://localhost:8000")
    print("3. Login with test users above")
    print("4. Follow: docs/tasks/AREA_CODE_MANUAL_TESTING_CHECKLIST.md")
    print("\n✅ Ready to begin testing!")


def verify_tier_configs(db: Session):
    """Verify subscription tier configurations exist."""

    print("\n🔍 Verifying Tier Configurations...")

    required_tiers = ["freemium", "payg", "pro", "custom"]

    for tier_name in required_tiers:
        tier = (
            db.query(SubscriptionTier)
            .filter(SubscriptionTier.tier == tier_name)
            .first()
        )

        if tier:
            has_area_code = getattr(tier, "has_area_code_selection", False)
            print(f"✅ {tier_name.upper()}: has_area_code_selection = {has_area_code}")
        else:
            print(f"⚠️  {tier_name.upper()}: Tier configuration not found")

    print()


def main():
    """Main function."""
    db = SessionLocal()

    try:
        # Verify tier configurations
        verify_tier_configs(db)

        # Create test users
        create_test_users(db)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    exit(main())
