#!/usr/bin/env python3
"""Setup demo admin user for local development."""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.utils.security import hash_password
import uuid

async def setup_demo_user():
    """Create demo admin user if it doesn't exist."""
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as db:
        try:
            # Check if demo user exists
            result = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "admin@namaskah.app"}
            ).fetchone()
            
            if result:
                print("✅ Demo admin user already exists")
                return
            
            # Create demo admin user
            user_id = str(uuid.uuid4())
            password_hash = hash_password("Namaskah@Admin2024")
            
            db.execute(
                text("""
                    INSERT INTO users (
                        id, email, password_hash, is_active, is_admin, 
                        email_verified, credits, free_verifications
                    ) VALUES (
                        :id, :email, :password_hash, :is_active, :is_admin,
                        :email_verified, :credits, :free_verifications
                    )
                """),
                {
                    "id": user_id,
                    "email": "admin@namaskah.app",
                    "password_hash": password_hash,
                    "is_active": True,
                    "is_admin": True,
                    "email_verified": True,
                    "credits": 100.0,
                    "free_verifications": 5.0
                }
            )
            
            db.commit()
            print("✅ Demo admin user created successfully!")
            print("📧 Email: admin@namaskah.app")
            print("🔑 Password: Namaskah@Admin2024")
            print("💰 Credits: $100.00")
            
        except Exception as e:
            print(f"❌ Error creating demo user: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(setup_demo_user())