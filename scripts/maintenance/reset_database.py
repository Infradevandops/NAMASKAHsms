#!/usr/bin/env python3
"""
Database Reset Script - Fix Schema Issues

This script recreates the database with the correct schema.
Use this when the database schema is out of sync with models.

Requires env vars:
  ADMIN_PASSWORD   — password for admin@vrenum.app
  TEST_PASSWORD    — password for test@example.com (optional, defaults to random)
"""

import os
import secrets
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import app.models.base
from app.core.database import Base, SessionLocal, engine
from app.models.user import User
from app.utils.security import get_password_hash


def reset_database():
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")


def create_admin_user():
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_password:
        raise RuntimeError("Set ADMIN_PASSWORD env var before running this script")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@vrenum.app").first()
        if existing:
            print("Admin user already exists")
            return

        admin = User(
            email="admin@vrenum.app",
            hashed_password=get_password_hash(admin_password),
            is_admin=True,
            is_active=True,
            email_verified=True,
            subscription_tier="custom",
            credits=1000.0,
            provider="email",
            language="en",
            currency="USD",
            terms_accepted=True,
        )
        db.add(admin)
        db.commit()
        print("Admin user created: admin@vrenum.app")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def create_test_user():
    test_password = os.environ.get("TEST_PASSWORD", secrets.token_urlsafe(16))

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if existing:
            existing.subscription_tier = "pro"
            existing.credits = 100.0
            db.commit()
            print("Test user upgraded to Pro tier")
            return

        test_user = User(
            email="test@example.com",
            hashed_password=get_password_hash(test_password),
            is_admin=False,
            is_active=True,
            email_verified=True,
            subscription_tier="pro",
            credits=100.0,
            provider="email",
            language="en",
            currency="USD",
            terms_accepted=True,
        )
        db.add(test_user)
        db.commit()
        print("Test user created: test@example.com")
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if not os.environ.get("ADMIN_PASSWORD"):
        print("ERROR: Set ADMIN_PASSWORD env var first")
        print("  export ADMIN_PASSWORD=your-secure-password")
        sys.exit(1)

    print("WARNING: All existing data will be lost!")
    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    reset_database()
    create_admin_user()
    create_test_user()
    print("Done.")
