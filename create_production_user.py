#!/usr/bin/env python3
"""Create production test user for Render deployment."""
import os
import sys
import asyncio
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import hash_password

async def create_production_user():
    """Create test user that works in production."""
    
    # Use production database URL if available
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./sms.db')
    
    # Handle PostgreSQL URL format for production
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Create engine
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Production test credentials
            test_users = [
                {
                    'email': 'demo@namaskah.app',
                    'password': 'demo2024!',
                    'credits': 25.0,
                    'free_verifications': 10,
                    'is_admin': True
                },
                {
                    'email': 'test@namaskah.app', 
                    'password': 'test123',
                    'credits': 10.0,
                    'free_verifications': 5,
                    'is_admin': False
                },
                {
                    'email': 'admin@namaskah.app',
                    'password': 'admin2024!',
                    'credits': 50.0,
                    'free_verifications': 20,
                    'is_admin': True
                }
            ]
            
            for user_data in test_users:
                # Check if user exists
                existing = session.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": user_data['email']}
                ).fetchone()
                
                if existing:
                    print(f"✅ User {user_data['email']} already exists")
                    continue
                
                # Create user
                user_id = str(uuid.uuid4())
                password_hash = hash_password(user_data['password'])
                
                session.execute(text("""
                    INSERT INTO users 
                    (id, email, password_hash, credits, free_verifications, is_admin, email_verified, created_at)
                    VALUES (:id, :email, :password_hash, :credits, :free_verifications, :is_admin, :email_verified, datetime('now'))
                """), {
                    'id': user_id,
                    'email': user_data['email'],
                    'password_hash': password_hash,
                    'credits': user_data['credits'],
                    'free_verifications': user_data['free_verifications'],
                    'is_admin': user_data['is_admin'],
                    'email_verified': True
                })
                
                session.commit()
                print(f"✅ Created user: {user_data['email']}")
            
            print("\n🎯 PRODUCTION TEST CREDENTIALS:")
            print("=" * 50)
            print("📧 Email: demo@namaskah.app")
            print("🔑 Password: demo2024!")
            print("💰 Credits: $25.00")
            print("🎫 Free Verifications: 10")
            print("👑 Admin: Yes")
            print()
            print("📧 Email: admin@namaskah.app") 
            print("🔑 Password: admin2024!")
            print("💰 Credits: $50.00")
            print("🎫 Free Verifications: 20")
            print("👑 Admin: Yes")
            print()
            print("📧 Email: test@namaskah.app")
            print("🔑 Password: test123")
            print("💰 Credits: $10.00")
            print("🎫 Free Verifications: 5")
            print("👑 Admin: No")
            
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        print("\n🔑 MANUAL CREDENTIALS (use these if script fails):")
        print("📧 Email: demo@namaskah.app")
        print("🔑 Password: demo2024!")

if __name__ == "__main__":
    asyncio.run(create_production_user())