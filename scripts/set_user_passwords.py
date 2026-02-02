#!/usr/bin/env python3
"""
import sys
from passlib.context import CryptContext
from app.core.database import SessionLocal
from app.models.user import User

Set known passwords for existing users
"""


sys.path.append(".")


def set_user_passwords():

    """Set known passwords for existing users."""

    print("🔐 SETTING USER PASSWORDS")
    print("=" * 40)

    db = SessionLocal()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Update existing users with known passwords
    user_passwords = {
        "test@namaskah.app": "test123",
        "test@example.com": "demo123",
        "test@flow.com": "flow123",
        "admin@namaskah.app": "admin123",  # Keep admin password
    }

    updated_users = []

for email, password in user_passwords.items():
        user = db.query(User).filter(User.email == email).first()

if user:
            # Update password
            user.password_hash = pwd_context.hash(password)
            user.email_verified = True

            # Get user details
            tier = getattr(user, "subscription_tier", "freemium") or "freemium"
            credits = getattr(user, "credits", 0) or 0
            is_admin = getattr(user, "is_admin", False)

            updated_users.append(
                {
                    "email": email,
                    "password": password,
                    "tier": tier,
                    "credits": credits,
                    "is_admin": is_admin,
                }
            )

            print(f"✅ Updated: {email}")
else:
            print(f"❌ Not found: {email}")

    db.commit()
    db.close()

    print("\n🎯 WORKING LOGIN CREDENTIALS:")
    print("=" * 40)

for user in updated_users:
        user_type = "👑 ADMIN" if user["is_admin"] else "👤 USER"
        print(f"{user_type}")
        print(f"   Email: {user['email']}")
        print(f"   Password: {user['password']}")
        print(f"   Tier: {user['tier'].title()}")
        print(f"   Credits: ${user['credits']:.2f}")
        print()

    print("🚀 DASHBOARD ACCESS:")
    print("   Login URL: http://localhost:8000/auth/login")
    print("   User Dashboard: http://localhost:8000/dashboard")
    print("   Admin Dashboard: http://localhost:8000/admin")
    print()
    print("✅ All credentials ready!")


if __name__ == "__main__":
    set_user_passwords()