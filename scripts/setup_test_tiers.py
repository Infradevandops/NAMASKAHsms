#!/usr/bin/env python3
"""
Setup Test User Tiers

Sets up test users with specific subscription tiers for testing the tier-based
RBAC system.

Usage:
    python scripts/setup_test_tiers.py setup     # Set all test user tiers
    python scripts/setup_test_tiers.py verify    # Verify test user tiers
    python scripts/setup_test_tiers.py list      # List all users and their tiers

Feature: tier-system-rbac
Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User

# Test user tier assignments
TEST_USER_TIERS = {
    "admin@namaskah.app": "freemium",
    "user@test.com": "freemium",
    "starter@test.com": "payg",
    "pro@test.com": "pro",
    "demo@namaskah.app": "custom",
}

VALID_TIERS = ["freemium", "payg", "pro", "custom"]


def setup_test_tiers(db: Session) -> dict:
    """Set subscription tiers for test users."""
    results = {"updated": [], "created": [], "not_found": [], "errors": []}

    for email, tier in TEST_USER_TIERS.items():
        try:
            user = db.query(User).filter(User.email == email).first()

            if user:
                old_tier = user.subscription_tier
                user.subscription_tier = tier
                db.commit()
                results["updated"].append(
                    {"email": email, "old_tier": old_tier, "new_tier": tier}
                )
                print(f"✓ Updated {email}: {old_tier} → {tier}")
            else:
                results["not_found"].append(email)
                print(f"⚠ User not found: {email}")

        except Exception as e:
            db.rollback()
            results["errors"].append({"email": email, "error": str(e)})
            print(f"✗ Error updating {email}: {e}")

    return results


def verify_test_tiers(db: Session) -> dict:
    """Verify test users have correct tiers."""
    results = {"correct": [], "incorrect": [], "not_found": []}

    print("\nVerifying test user tiers:")
    print("-" * 50)

    for email, expected_tier in TEST_USER_TIERS.items():
        user = db.query(User).filter(User.email == email).first()

        if user:
            actual_tier = user.subscription_tier or "freemium"
            if actual_tier == expected_tier:
                results["correct"].append(email)
                print(f"✓ {email}: {actual_tier} (correct)")
            else:
                results["incorrect"].append(
                    {"email": email, "expected": expected_tier, "actual": actual_tier}
                )
                print(f"✗ {email}: {actual_tier} (expected: {expected_tier})")
        else:
            results["not_found"].append(email)
            print(f"⚠ {email}: NOT FOUND")

    print("-" * 50)
    print(
        f"Correct: {len(results['correct'])}, Incorrect: {len(results['incorrect'])}, Not Found: {len(results['not_found'])}"
    )

    return results


def list_all_users(db: Session) -> list:
    """List all users and their tiers."""
    users = db.query(User).order_by(User.email).all()

    print("\nAll Users and Tiers:")
    print("-" * 60)
    print(f"{'Email':<35} {'Tier':<15} {'Admin':<6}")
    print("-" * 60)

    for user in users:
        tier = user.subscription_tier or "freemium"
        admin = "Yes" if user.is_admin else "No"
        print(f"{user.email:<35} {tier:<15} {admin:<6}")

    print("-" * 60)
    print(f"Total users: {len(users)}")

    return [
        {"email": u.email, "tier": u.subscription_tier, "is_admin": u.is_admin}
        for u in users
    ]


def create_test_users(db: Session) -> dict:
    """Create missing test users."""
    from app.core.security import get_password_hash

    results = {"created": [], "exists": [], "errors": []}

    for email, tier in TEST_USER_TIERS.items():
        try:
            existing = db.query(User).filter(User.email == email).first()

            if existing:
                results["exists"].append(email)
                continue

            # Create new user
            user = User(
                email=email,
                hashed_password=get_password_hash("TestPassword123!"),
                subscription_tier=tier,
                is_active=True,
                is_admin=email.endswith("@namaskah.app"),
            )
            db.add(user)
            db.commit()

            results["created"].append({"email": email, "tier": tier})
            print(f"✓ Created {email} with tier {tier}")

        except Exception as e:
            db.rollback()
            results["errors"].append({"email": email, "error": str(e)})
            print(f"✗ Error creating {email}: {e}")

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/setup_test_tiers.py <command>")
        print("\nCommands:")
        print("  setup    - Set subscription tiers for test users")
        print("  verify   - Verify test users have correct tiers")
        print("  list     - List all users and their tiers")
        print("  create   - Create missing test users")
        sys.exit(1)

    command = sys.argv[1].lower()

    db = SessionLocal()
    try:
        if command == "setup":
            print("Setting up test user tiers...")
            results = setup_test_tiers(db)
            print(
                f"\nSummary: {len(results['updated'])} updated, {len(results['not_found'])} not found"
            )

        elif command == "verify":
            verify_test_tiers(db)

        elif command == "list":
            list_all_users(db)

        elif command == "create":
            print("Creating missing test users...")
            results = create_test_users(db)
            print(
                f"\nSummary: {len(results['created'])} created, {len(results['exists'])} already exist"
            )

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
