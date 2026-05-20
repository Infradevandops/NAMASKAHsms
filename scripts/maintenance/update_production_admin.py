#!/usr/bin/env python3
"""
Update admin user credentials in production database
"""

import os
import sys
import bcrypt
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_production_admin():
    """Update admin user in production PostgreSQL database"""

    # Import after path is set
    from sqlalchemy import create_engine, text

    # Production database URL
    DATABASE_URL = "postgresql://namaskahdb:mT7K2xu1EZyrb6r8ER5pbpWGEffMyPW5@dpg-d7geq9vlk1mc7386tjl0-a.frankfurt-postgres.render.com/namaskahdb_qg9v"

    print("🔧 Connecting to production database...")
    engine = create_engine(DATABASE_URL)

    email = "admin@vrenum.app"
    password = "Namaskah@Admin2024"

    # Hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    with engine.connect() as conn:
        # Check if admin user exists
        result = conn.execute(
            text("SELECT id, email, is_admin, credits FROM users WHERE email = :email OR is_admin = true"),
            {"email": email}
        )
        admin = result.fetchone()

        if admin:
            print(f"✅ Found admin user: {admin[1]}")
            print(f"   ID: {admin[0]}")
            print(f"   Is Admin: {admin[2]}")
            print(f"   Credits: {admin[3]}")

            # Update the admin user
            conn.execute(
                text("""
                    UPDATE users
                    SET email = :new_email,
                        password_hash = :password_hash,
                        updated_at = :updated_at,
                        email_verified = true,
                        is_admin = true
                    WHERE id = :user_id
                """),
                {
                    "new_email": email,
                    "password_hash": password_hash,
                    "updated_at": datetime.now(),
                    "user_id": admin[0]
                }
            )
            conn.commit()

            # Verify the update
            result = conn.execute(
                text("SELECT email, is_admin FROM users WHERE id = :user_id"),
                {"user_id": admin[0]}
            )
            updated = result.fetchone()

            if updated and updated[0] == email:
                print(f"\n✅ Admin user updated successfully!")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                print(f"   Is Admin: {updated[1]}")
                print(f"\n🎉 You can now login at: https://vrenum.onrender.com/login")
            else:
                print("❌ Update verification failed")
        else:
            print("❌ No admin user found in production database")
            print("   Creating new admin user...")

            # Create admin user
            import uuid
            user_id = str(uuid.uuid4())

            conn.execute(
                text("""
                    INSERT INTO users (
                        id, email, password_hash, is_admin, email_verified,
                        subscription_tier, credits, created_at, updated_at
                    ) VALUES (
                        :id, :email, :password_hash, true, true,
                        'custom', 0, :created_at, :updated_at
                    )
                """),
                {
                    "id": user_id,
                    "email": email,
                    "password_hash": password_hash,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )
            conn.commit()

            print(f"✅ Admin user created!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")

if __name__ == "__main__":
    try:
        update_production_admin()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
