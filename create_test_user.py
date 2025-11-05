#!/usr/bin/env python3
"""Create test user for local testing."""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import hash_password

async def create_test_user():
    # Create async engine
    engine = create_async_engine("sqlite+aiosqlite:///./sms.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        existing = await session.get(User, "test@namaskah.app")
        if existing:
            print("✅ Test user already exists")
            return
        
        # Create test user
        user = User(
            id=str(uuid.uuid4()),
            email="test@namaskah.app",
            password_hash=hash_password("test123"),
            credits=10.0,
            free_verifications=5,
            is_admin=True,
            email_verified=True
        )
        
        session.add(user)
        await session.commit()
        
        print("✅ Test user created successfully!")
        print("📧 Email: test@namaskah.app")
        print("🔑 Password: test123")
        print("💰 Credits: 10.0")

if __name__ == "__main__":
    asyncio.run(create_test_user())