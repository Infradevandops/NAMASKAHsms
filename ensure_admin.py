#!/usr/bin/env python3
"""Ensure admin user exists in database."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import hash_password

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./namaskah.db")

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("Checking for admin user...")

# Check if admin exists
admin = db.query(User).filter(User.email == "admin@namaskah.app").first()

if admin:
    print(f"✅ Admin user exists: {admin.email}")
    print(f"   ID: {admin.id}")
    print(f"   Admin: {admin.is_admin}")
    print(f"   Verified: {admin.email_verified}")
else:
    print("❌ Admin user not found. Creating...")
    
    admin = User(
        email="admin@namaskah.app",
        password_hash=hash_password("admin123"),
        is_admin=True,
        email_verified=True,
        credits=1000.0
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✅ Admin user created: {admin.email}")
    print(f"   Password: admin123")
    print(f"   ID: {admin.id}")

db.close()
print("\n✅ Done!")
