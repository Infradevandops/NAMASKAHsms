#!/usr/bin/env python3
"""
Update admin credentials - Run this ON Render server
Usage: python3 update_admin_production.py
"""

import os
from datetime import datetime

import bcrypt
from sqlalchemy import create_engine, text


def main():
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return

    print("🔧 Updating admin credentials in production...")

    email = "admin@vrenum.app"
    password = "Namaskah@Admin2024"

    # Hash the password
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Find admin user
        result = conn.execute(
            text(
                "SELECT id, email, is_admin, credits FROM users WHERE is_admin = true LIMIT 1"
            )
        )
        admin = result.fetchone()

        if admin:
            print(f"✅ Found admin user: {admin.email}")
            print(f"   ID: {admin.id}")
            print(f"   Credits: {admin.credits}")

            # Update credentials
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET email = :email,
                        password_hash = :password_hash,
                        email_verified = true,
                        is_admin = true,
                        is_active = true,
                        updated_at = :updated_at
                    WHERE id = :user_id
                """
                ),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "updated_at": datetime.now(),
                    "user_id": admin.id,
                },
            )
            conn.commit()

            print(f"\n✅ Admin credentials updated!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"\n🎉 Login at: https://vrenum.onrender.com/login")
        else:
            print("❌ No admin user found")


if __name__ == "__main__":
    main()
