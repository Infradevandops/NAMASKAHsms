#!/usr/bin/env python3
"""Test login credentials directly"""

from app.core.database import get_db
from app.models.user import User
import bcrypt

def test_credentials():
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if not user:
            print("❌ User not found")
            return False
        
        print(f"✅ User found: {user.email}")
        print(f"   Admin: {user.is_admin}")
        print(f"   Email verified: {user.email_verified}")
        
        # Test password
        password = "NamaskahAdmin2024!"
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            print("✅ Password matches")
            return True
        else:
            print("❌ Password doesn't match")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_credentials()