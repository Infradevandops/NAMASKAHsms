#!/usr/bin/env python3
"""
Test admin credentials using SQLite database
Run this when the server won't start but you want to verify credentials
"""

import sqlite3
import bcrypt
import os

def test_admin_credentials():
    """Test admin credentials in SQLite database"""
    
    # Check if SQLite database exists
    db_path = "namaskah.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"🔍 Testing credentials in {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found")
            return
        
        # Find admin user
        cursor.execute("SELECT id, email, password_hash, is_admin, credits, subscription_tier FROM users WHERE email = ?", 
                      ("admin@namaskah.app",))
        user = cursor.fetchone()
        
        if user:
            user_id, email, password_hash, is_admin, credits, tier = user
            print(f"✅ User found: {email}")
            print(f"   ID: {user_id}")
            print(f"   Is Admin: {bool(is_admin)}")
            print(f"   Credits: {credits}")
            print(f"   Tier: {tier}")
            
            # Test password
            if password_hash:
                password_bytes = "Namaskah@Admin2024".encode('utf-8')
                hash_bytes = password_hash.encode('utf-8')
                
                try:
                    password_valid = bcrypt.checkpw(password_bytes, hash_bytes)
                    print(f"   Password Valid: {password_valid}")
                    
                    if password_valid:
                        print("🎉 Admin credentials are correct!")
                        
                        # Check for notifications
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='notifications'")
                        if cursor.fetchone()[0]:
                            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ?", (user_id,))
                            notif_count = cursor.fetchone()[0]
                            print(f"   Notifications: {notif_count}")
                        
                        # Check for verifications
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='verifications'")
                        if cursor.fetchone()[0]:
                            cursor.execute("SELECT COUNT(*) FROM verifications WHERE user_id = ?", (user_id,))
                            verify_count = cursor.fetchone()[0]
                            print(f"   Verifications: {verify_count}")
                        
                    else:
                        print("❌ Password is incorrect")
                        
                except Exception as e:
                    print(f"   Password check error: {e}")
            else:
                print("   No password hash found")
        else:
            print("❌ Admin user not found")
            
            # Check total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            print(f"Total users in database: {total_users}")
            
            if total_users > 0:
                cursor.execute("SELECT email FROM users LIMIT 5")
                users = cursor.fetchall()
                print("Sample users:")
                for user_email in users:
                    print(f"  - {user_email[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_admin_credentials()