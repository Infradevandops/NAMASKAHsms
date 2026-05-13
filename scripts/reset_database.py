#!/usr/bin/env python3
"""
Database Reset Script - Fix Schema Issues

This script recreates the database with the correct schema.
Use this when the database schema is out of sync with models.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all models to ensure relationships are loaded
import app.models.base  # Import base first
from app.core.database import Base, SessionLocal, engine
from app.models.user import User
from app.utils.security import get_password_hash


def reset_database():
    """Drop all tables and recreate with current schema"""
    print("🔄 Resetting database...")

    # Drop all tables
    print("   Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    # Create all tables with current schema
    print("   Creating tables with current schema...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database reset complete!")


def create_admin_user():
    """Create default admin user"""

    print("\n👤 Creating admin user...")

    db = SessionLocal()
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if existing:
            print("   Admin user already exists")
            return

        # Create admin user
        admin = User(
            email="admin@namaskah.app",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
            is_active=True,
            email_verified=True,
            subscription_tier="custom",
            credits=1000.0,
            provider="email",
            language="en",
            currency="USD",
            terms_accepted=True,  # Set terms_accepted
        )

        db.add(admin)
        db.commit()

        print("✅ Admin user created!")
        print("   Email: admin@namaskah.app")
        print("   Password: admin123")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def create_test_user():
    """Create test user for Phase 2 testing"""

    print("\n👤 Creating test user...")

    db = SessionLocal()
    try:
        # Check if test user exists
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if existing:
            print("   Test user already exists")
            # Upgrade to Pro tier
            existing.subscription_tier = "pro"
            existing.credits = 100.0
            db.commit()
            print("   Upgraded to Pro tier with 100 credits")
            return

        # Create test user
        test_user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            is_admin=False,
            is_active=True,
            email_verified=True,
            subscription_tier="pro",  # Pro tier for email templates
            credits=100.0,
            provider="email",
            language="en",
            currency="USD",
            terms_accepted=True,
        )

        db.add(test_user)
        db.commit()

        print("✅ Test user created!")
        print("   Email: test@example.com")
        print("   Password: testpassword123")
        print("   Tier: Pro")
        print("   Credits: 100.0")

    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Drop all existing tables")
    print("  2. Recreate tables with current schema")
    print("  3. Create admin user (admin@namaskah.app / admin123)")
    print("  4. Create test user (test@example.com / testpassword123)")
    print("\n⚠️  WARNING: All existing data will be lost!")

    response = input("\nContinue? (yes/no): ")
    if response.lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    try:
        reset_database()
        create_admin_user()
        create_test_user()

        print("\n" + "=" * 60)
        print("✅ DATABASE RESET COMPLETE!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start server: uvicorn main:app --reload")
        print("  2. Login as admin: admin@namaskah.app / admin123")
        print("  3. Login as test user: test@example.com / testpassword123")
        print("  4. Run Phase 2 tests: python tests/manual/test_email_templates.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
