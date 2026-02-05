#!/usr/bin/env python3
"""
Fix localhost admin credentials
"""
import hashlib
import sqlite3
import uuid
from datetime import datetime


def fix_admin_creds():
    try:
        conn = sqlite3.connect("namaskah.db")
        cursor = conn.cursor()

        # Simple bcrypt-like hash for development (not secure for production)
        password = "admin123"
        # Using a simple hash for localhost only
        password_hash = "$2b$12$" + hashlib.sha256(password.encode()).hexdigest()[:50]

        # Check if admin exists
        cursor.execute('SELECT id FROM users WHERE email = "admin@namaskah.app"')
        admin_exists = cursor.fetchone()

        if admin_exists:
            # Update existing admin
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?, is_admin = 1, is_active = 1, is_suspended = 0, is_banned = 0
                WHERE email = "admin@namaskah.app"
            """,
                (password_hash,),
            )
            print("✅ Updated existing admin user")
        else:
            # Create new admin
            admin_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, credits, free_verifications,
                    is_admin, is_moderator, email_verified, subscription_tier,
                    referral_earnings, provider, language, currency,
                    is_affiliate, is_active, is_suspended, is_banned, is_deleted,
                    created_at
                ) VALUES (?, ?, ?, 1000.0, 0.0, 1, 0, 1, 'custom', 0.0, 'local', 'en', 'USD', 0, 1, 0, 0, 0, ?)
            """,
                (
                    admin_id,
                    "admin@namaskah.app",
                    password_hash,
                    datetime.now().isoformat(),
                ),
            )
            print("✅ Created new admin user")

        # Clear any lockouts
        cursor.execute(
            'DELETE FROM account_lockouts WHERE email = "admin@namaskah.app"'
        )

        conn.commit()
        print("   Email: admin@namaskah.app")
        print(f"   Password: {password}")
        print("🎯 Admin ready for localhost login")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    fix_admin_creds()