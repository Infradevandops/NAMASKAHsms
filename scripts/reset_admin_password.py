#!/usr/bin/env python3
"""Reset admin password using environment variable."""


# Add app to path

import os
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password, verify_password
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reset_admin_password():

    """Reset admin password from ADMIN_PASSWORD env var."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")
    admin_password = os.getenv("ADMIN_PASSWORD")

if not admin_password:
        print("❌ ADMIN_PASSWORD environment variable not set!")
        print(
            "Usage: ADMIN_PASSWORD='your-password' python scripts/reset_admin_password.py"
        )
        sys.exit(1)

    db = SessionLocal()
try:
        # Find admin user
        admin = db.query(User).filter(User.email == admin_email).first()

if not admin:
            print(f"❌ Admin user not found: {admin_email}")
            print("Creating new admin user...")

            admin = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                credits=10000.0,
                is_admin=True,
                email_verified=True,
                free_verifications=1000.0,
                subscription_tier="custom",
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin user created: {admin_email}")
else:
            # Update password
            old_hash = admin.password_hash
            new_hash = hash_password(admin_password)

            admin.password_hash = new_hash
            admin.is_admin = True
            admin.email_verified = True
            admin.subscription_tier = "custom"
            admin.credits = max(admin.credits, 10000.0)

            db.commit()

            print(f"✅ Admin password updated: {admin_email}")
            print(f"   Old hash: {old_hash[:30]}...")
            print(f"   New hash: {new_hash[:30]}...")

            # Verify the password works
if verify_password(admin_password, new_hash):
                print("✅ Password verification successful!")
else:
                print("❌ Password verification failed!")

        # Test login
        print(f"\n📧 Admin Email: {admin_email}")
        print(f"🔑 Password Length: {len(admin_password)} chars")
        print(f"🔐 Password Hash: {admin.password_hash[:50]}...")
        print(f"👤 Is Admin: {admin.is_admin}")
        print(f"✉️  Email Verified: {admin.email_verified}")
        print(f"🎫 Tier: {admin.subscription_tier}")
        print(f"💰 Credits: {admin.credits}")

except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()
        db.rollback()
        sys.exit(1)
finally:
        db.close()


if __name__ == "__main__":
    reset_admin_password()
