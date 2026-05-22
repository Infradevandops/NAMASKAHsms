#!/usr/bin/env python3
"""Check admin user status."""


# Add app to path

import os
import sys
import traceback

from app.core.database import SessionLocal
from app.models.user import User

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_admin():

    """Check admin user status."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@vrenum.app")

    db = SessionLocal()
try:
        admin = db.query(User).filter(User.email == admin_email).first()

if not admin:
            print(f"❌ No admin user found with email: {admin_email}")
            print("\nSearching for any admin users...")
            admins = db.query(User).filter(User.is_admin).all()
if admins:
                print(f"\n✅ Found {len(admins)} admin user(s):")
for a in admins:
                    print(f"   - {a.email} (ID: {a.id})")
else:
                print("❌ No admin users found in database")
            return

        print(f"✅ Admin user found: {admin_email}")
        print("\n📊 Admin User Details:")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Is Admin: {admin.is_admin}")
        print(f"   Email Verified: {admin.email_verified}")
        print(f"   Tier: {admin.subscription_tier}")
        print(f"   Credits: {admin.credits}")
        print(f"   Has Password Hash: {bool(admin.password_hash)}")
if admin.password_hash:
            print(f"   Password Hash (first 50 chars): {admin.password_hash[:50]}...")
        print(f"   Is Active: {getattr(admin, 'is_active', 'N/A')}")
        print(f"   Is Suspended: {getattr(admin, 'is_suspended', 'N/A')}")
        print(f"   Is Banned: {getattr(admin, 'is_banned', 'N/A')}")

except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()
finally:
        db.close()


if __name__ == "__main__":
    check_admin()
