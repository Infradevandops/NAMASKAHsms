#!/usr/bin/env python3
"""Simple login test"""

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import get_auth_service
import bcrypt

def test_login(email: str, password: str):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User {email} not found")
            return False
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            print(f"✅ Login successful for {email}")
            print(f"   Admin: {user.is_admin}")
            print(f"   Credits: {user.credits}")
            return True
        else:
            print(f"❌ Wrong password for {email}")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing login credentials...")
    test_login("admin@namaskah.app", "admin123")
    test_login("test@example.com", "password")