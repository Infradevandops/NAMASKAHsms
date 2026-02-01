#!/usr/bin/env python3
"""
import sqlite3
import bcrypt
import uuid
from datetime import datetime

Initialize admin user in SQLite database
"""


def create_admin_user():

    """Create admin user in SQLite database"""

    db_path = "namaskah.db"
    email = "admin@namaskah.app"
    password = "Namaskah@Admin2024"

    print(f"🔧 Creating admin user in {db_path}")

try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                credits REAL DEFAULT 0.0,
                free_verifications REAL DEFAULT 1.0,
                is_admin BOOLEAN DEFAULT FALSE,
                is_moderator BOOLEAN DEFAULT FALSE,
                email_verified BOOLEAN DEFAULT FALSE,
                subscription_tier TEXT DEFAULT 'freemium',
                referral_code TEXT,
                referred_by TEXT,
                referral_earnings REAL DEFAULT 0.0,
                google_id TEXT,
                provider TEXT DEFAULT 'email',
                avatar_url TEXT,
                refresh_token TEXT,
                refresh_token_expires DATETIME,
                last_login DATETIME,
                failed_login_attempts INTEGER DEFAULT 0,
                subscription_start_date DATETIME,
                language TEXT DEFAULT 'en',
                currency TEXT DEFAULT 'USD',
                affiliate_id TEXT,
                partner_type TEXT,
                commission_tier TEXT,
                is_affiliate BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_at DATETIME,
                suspension_reason TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                banned_at DATETIME,
                ban_reason TEXT,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at DATETIME,
                deletion_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                link TEXT,
                icon TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create verifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                service_name TEXT NOT NULL,
                capability TEXT DEFAULT 'sms',
                status TEXT DEFAULT 'pending',
                cost REAL NOT NULL,
                phone_number TEXT,
                country TEXT DEFAULT 'US',
                activation_id TEXT,
                provider TEXT DEFAULT 'textverified',
                requested_area_code TEXT,
                requested_carrier TEXT,
                operator TEXT,
                sms_code TEXT,
                sms_text TEXT,
                idempotency_key TEXT,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

if existing_user:
            print(f"✅ Admin user already exists: {email}")
            user_id = existing_user[0]
else:
            # Hash password
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

            # Generate user ID
            user_id = str(uuid.uuid4())

            # Insert admin user with all required fields based on actual schema
            cursor.execute("""
                INSERT INTO users (
                    id, email, password_hash, credits, free_verifications,
                    is_admin, is_moderator, email_verified, subscription_tier,
                    bonus_sms_balance, monthly_quota_used, referral_earnings,
                    provider, language, currency, is_affiliate, is_active,
                    is_suspended, is_banned, is_deleted, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, email, password_hash, 100.0, 1.0, True, False, True, 'custom',
                  0.0, 0.0, 0.0, 'email', 'en', 'USD', False, True, False, False, False, datetime.now()))

            print(f"✅ Created admin user: {email}")

        # Create a test notification
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ?", (user_id,))
        notif_count = cursor.fetchone()[0]

if notif_count == 0:
            notif_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notifications (id, user_id, type, title, message, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (notif_id, user_id, 'welcome', '🎉 Welcome to Namaskah!',
                  'Your admin account has been created successfully.', False, datetime.now()))
            print("✅ Created test notification")

        # Create a test verification
        cursor.execute("SELECT COUNT(*) FROM verifications WHERE user_id = ?", (user_id,))
        verify_count = cursor.fetchone()[0]

if verify_count == 0:
            verify_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO verifications (
                    id, user_id, service_name, capability, status, cost,
                    phone_number, country, sms_code, sms_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (verify_id, user_id, 'telegram', 'sms', 'completed', 2.22,
                  '+12125551234', 'US', '123456', 'Your verification code is 123456', datetime.now()))
            print("✅ Created test verification")

        conn.commit()
        conn.close()

        print("""
🎉 Setup complete!

Admin credentials:
  Email: {email}
  Password: {password}
  User ID: {user_id}
  Credits: 100.0
  Tier: custom

You can now test:
1. Start server: python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
2. Test login: ./test_admin_login.sh
3. Visit: http://127.0.0.1:8000/login
        """)

except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin_user()