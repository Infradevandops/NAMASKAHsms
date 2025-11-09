#!/usr/bin/env python3
"""Create admin user with credits for testing."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_admin_user():
    """Create admin user with testing credits."""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.utils.security import hash_password

        db = SessionLocal()

        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()

        if admin:
            print("✅ Admin user already exists")
            print(f"Email: admin@namaskah.app")
            print(f"Credits: {admin.credits}")
            return

        # Create admin user
        admin_user = User(
            email="admin@namaskah.app",
            password_hash=hash_password("admin123"),
            credits=1000.0,  # 1000 credits for testing
            is_admin=True,
            email_verified=True,
        )

        db.add(admin_user)
        db.commit()

        print("✅ Admin user created successfully!")
        print("Email: admin@namaskah.app")
        print("Password: admin123")
        print("Credits: 1000.0")
        print("Admin: Yes")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
