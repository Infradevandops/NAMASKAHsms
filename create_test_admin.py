#!/usr/bin/env python3
"""Create test admin user for local development."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import User
from app.utils.security import hash_password

async def create_admin():
    settings = get_settings()
    
    # Convert SQLite URL for async
    db_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin exists
        admin = await session.get(User, 1)
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            id=1,
            email="admin@test.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            is_active=True,
            is_admin=True,
            is_verified=True
        )
        
        session.add(admin_user)
        await session.commit()
        print("✅ Admin user created: admin@test.com / admin123")

if __name__ == "__main__":
    asyncio.run(create_admin())