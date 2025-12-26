#!/usr/bin/env python3
"""
Create test user credentials for dashboard access
"""

import os
import sys
sys.path.append('.')

from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

def create_test_users():
    """Create test users with known passwords."""
    
    print("🔐 CREATING TEST USER CREDENTIALS")
    print("=" * 50)
    
    db = SessionLocal()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Test users to create/update
    test_users = [
        {
            "email": "user@test.com",
            "password": "password123",
            "tier": "payg",
            "credits": 50.0,
            "is_admin": False
        },
        {
            "email": "starter@test.com", 
            "password": "starter123",
            "tier": "starter",
            "credits": 25.0,
            "is_admin": False
        },
        {
            "email": "pro@test.com",
            "password": "pro123", 
            "tier": "pro",
            "credits": 100.0,
            "is_admin": False
        },
        {
            "email": "demo@namaskah.app",
            "password": "demo123",
            "tier": "payg", 
            "credits": 10.0,
            "is_admin": False
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            # Update existing user
            existing_user.password_hash = pwd_context.hash(user_data["password"])
            existing_user.tier_id = user_data["tier"]
            existing_user.credits = user_data["credits"]
            existing_user.is_admin = user_data["is_admin"]
            existing_user.email_verified = True
            
            print(f"✅ Updated: {user_data['email']}")
        else:
            # Create new user
            new_user = User(
                email=user_data["email"],
                password_hash=pwd_context.hash(user_data["password"]),
                tier_id=user_data["tier"],
                credits=user_data["credits"],
                is_admin=user_data["is_admin"],
                email_verified=True
            )
            db.add(new_user)
            print(f"✅ Created: {user_data['email']}")
        
        created_users.append({
            "email": user_data["email"],
            "password": user_data["password"],
            "tier": user_data["tier"],
            "credits": user_data["credits"]
        })
    
    db.commit()
    db.close()
    
    print("\n🎯 TEST USER CREDENTIALS READY:")
    print("=" * 50)
    
    for user in created_users:
        print(f"📧 Email: {user['email']}")
        print(f"   Password: {user['password']}")
        print(f"   Tier: {user['tier'].title()}")
        print(f"   Credits: ${user['credits']:.2f}")
        print()
    
    print("🚀 DASHBOARD ACCESS:")
    print("   URL: http://localhost:8000/auth/login")
    print("   Then: http://localhost:8000/dashboard")
    print()
    print("✅ All users ready for testing!")

if __name__ == "__main__":
    create_test_users()