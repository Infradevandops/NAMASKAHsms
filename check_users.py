#!/usr/bin/env python3
"""Check all users in database and verify credentials."""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import verify_password, hash_password

# Database connection
engine = create_engine("sqlite:///./namaskah.db")
Session = sessionmaker(bind=engine)
db = Session()

print("\n" + "="*60)
print("NAMASKAH USER DATABASE CHECK")
print("="*60 + "\n")

# Get all users
users = db.query(User).all()

if not users:
    print("❌ No users found in database!\n")
    print("Creating admin user...")
    
    admin = User(
        email="admin@namaskah.app",
        password_hash=hash_password("admin123"),
        is_admin=True,
        email_verified=True,
        credits=1000.0,
        free_verifications=10.0
    )
    db.add(admin)
    db.commit()
    print("✅ Admin user created: admin@namaskah.app / admin123\n")
    users = [admin]

print(f"Found {len(users)} user(s):\n")

for i, user in enumerate(users, 1):
    print(f"{i}. Email: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Admin: {'✅ Yes' if user.is_admin else '❌ No'}")
    print(f"   Email Verified: {'✅ Yes' if user.email_verified else '❌ No'}")
    print(f"   Credits: ${user.credits:.2f}")
    print(f"   Free Verifications: {user.free_verifications}")
    print(f"   Has Password: {'✅ Yes' if user.password_hash else '❌ No'}")
    
    if user.password_hash:
        # Test common passwords
        test_passwords = ["admin123", "password", "123456", "admin"]
        for pwd in test_passwords:
            if verify_password(pwd, user.password_hash):
                print(f"   ✅ PASSWORD WORKS: {pwd}")
                break
        else:
            print(f"   ⚠️  Password not in common list")
    
    print()

print("="*60)
print("\n🔑 WORKING CREDENTIALS:\n")

for user in users:
    if user.password_hash:
        for pwd in ["admin123", "password", "123456", "admin"]:
            if verify_password(pwd, user.password_hash):
                print(f"✅ {user.email} / {pwd}")
                if user.is_admin:
                    print(f"   → Admin Dashboard Access")
                break

print("\n" + "="*60 + "\n")

db.close()
