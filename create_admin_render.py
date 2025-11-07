#!/usr/bin/env python3
"""Create admin user for Render deployment."""

import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import User
from app.utils.security import hash_password

async def create_admin():
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin exists
        admin = await session.get(User, 1)
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user with environment variables or defaults
        admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "SecureAdmin123!")
        
        admin_user = User(
            id=1,
            email=admin_email,
            username="admin",
            hashed_password=hash_password(admin_password),
            is_active=True,
            is_admin=True,
            is_verified=True,
        )
        
        session.add(admin_user)
        await session.commit()
        print(f"✅ Admin user created: {admin_email}")

if __name__ == "__main__":
    asyncio.run(create_admin())