#!/usr/bin/env python3
"""Create test user with working credentials"""

from app.core.database import get_db
from app.models.user import User
import bcrypt
import uuid

def create_test_user():
    db = next(get_db())
    try:
        # Delete existing test user
        existing = db.query(User).filter(User.email == "demo@test.com").first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # Create new user
        password_hash = bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            id=str(uuid.uuid4()),
            email="demo@test.com",
            password_hash=password_hash,
            is_admin=True,
            credits=100.0,
            free_verifications=10,
            email_verified=True
        )
        
        db.add(user)
        db.commit()
        
        print("✅ Created test user:")
        print("   Email: demo@test.com")
        print("   Password: demo123")
        print("   Admin: True")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()