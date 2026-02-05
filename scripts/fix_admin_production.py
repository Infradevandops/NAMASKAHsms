#!/usr/bin/env python3
"""Fix admin user in production database."""

import os
import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Admin credentials
ADMIN_EMAIL = "admin@namaskah.app"
ADMIN_PASSWORD = "Namaskah@Admin2024"

# Hash password
password_hash = pwd_context.hash(ADMIN_PASSWORD)

print(f"Fixing admin user: {ADMIN_EMAIL}")
print(f"Password hash: {password_hash[:50]}...")

with engine.connect() as conn:
    # Check if user exists
    result = conn.execute(
        text("SELECT id, email, is_admin FROM users WHERE email = :email"),
        {"email": ADMIN_EMAIL}
    )
    user = result.fetchone()
    
    if user:
        print(f"✅ User exists: ID={user[0]}, Admin={user[2]}")
        
        # Update password
        conn.execute(
            text("UPDATE users SET password_hash = :hash, is_admin = true WHERE email = :email"),
            {"hash": password_hash, "email": ADMIN_EMAIL}
        )
        conn.commit()
        print("✅ Password updated")
    else:
        print("❌ User not found - creating...")
        
        # Create user
        conn.execute(
            text("""
                INSERT INTO users (email, password_hash, is_admin, credits, email_verified, created_at)
                VALUES (:email, :hash, true, 1000, true, NOW())
            """),
            {"email": ADMIN_EMAIL, "hash": password_hash}
        )
        conn.commit()
        print("✅ Admin user created")

print("\n✅ Done! Try logging in with:")
print(f"   Email: {ADMIN_EMAIL}")
print(f"   Password: {ADMIN_PASSWORD}")
