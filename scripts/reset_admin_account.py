#!/usr/bin/env python3
"""
Reset admin account lockout and create proper admin user
"""
import os
import sqlite3
import sys
from datetime import datetime

from passlib.context import CryptContext

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def reset_admin_account():
    try:
        conn = sqlite3.connect("namaskah.db")
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("⚠️  Database is empty - no tables found")
            print("   Run the application first to create tables")
            return

        print(f"Found tables: {', '.join(tables)}")

        # Clear account lockouts if table exists
        if "account_lockouts" in tables:
            cursor.execute(
                'DELETE FROM account_lockouts WHERE email = "admin@namaskah.app"'
            )
            print(f"✅ Cleared {cursor.rowcount} admin account lockouts")

        # Create/update admin user if users table exists
        if "users" in tables:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_password = "admin123"  # Simple password for development
            hashed_password = pwd_context.hash(admin_password)

            # Check if admin exists
            cursor.execute('SELECT id FROM users WHERE email = "admin@namaskah.app"')
            admin_exists = cursor.fetchone()

            if admin_exists:
                # Update existing admin
                cursor.execute(
                    """
                    UPDATE users 
                    SET password_hash = ?, is_admin = 1, is_active = 1
                    WHERE email = "admin@namaskah.app"
                """,
                    (hashed_password,),
                )
                print("✅ Updated existing admin user")
            else:
                # Create new admin
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, is_admin, is_active, credits, tier, created_at)
                    VALUES (?, ?, 1, 1, 1000.0, 'custom', ?)
                """,
                    ("admin@namaskah.app", hashed_password, datetime.now().isoformat()),
                )
                print("✅ Created new admin user")

            print(f"   Email: admin@namaskah.app")
            print(f"   Password: {admin_password}")

        conn.commit()
        print("\n🎯 Admin account ready for login")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    reset_admin_account()
