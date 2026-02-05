#!/usr/bin/env python3
"""Login diagnostic script - tests authentication and identifies issues."""

import sys
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Test credentials (passed as arguments)
if len(sys.argv) < 3:
    print("Usage: python3 test_login.py <email> <password>")
    sys.exit(1)

TEST_EMAIL = sys.argv[1]
TEST_PASSWORD = sys.argv[2]

print(f"🔍 Testing login for: {TEST_EMAIL}")
print("=" * 60)

# Connect to database
try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Check if user exists
print(f"\n1️⃣ Checking if user exists...")
try:
    result = db.execute(
        text("SELECT id, email, password_hash, is_admin, is_active, email_verified FROM users WHERE email = :email"),
        {"email": TEST_EMAIL}
    ).fetchone()
    
    if not result:
        print(f"❌ User not found: {TEST_EMAIL}")
        print("\n🔧 Fix: Create user with:")
        print(f"   psql $DATABASE_URL -c \"INSERT INTO users (email, password_hash, is_admin, is_active, email_verified) VALUES ('{TEST_EMAIL}', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJfLKZvSu', true, true, true);\"")
        sys.exit(1)
    
    user_id, email, password_hash, is_admin, is_active, email_verified = result
    print(f"✅ User found: {email}")
    print(f"   - ID: {user_id}")
    print(f"   - Admin: {is_admin}")
    print(f"   - Active: {is_active}")
    print(f"   - Email Verified: {email_verified}")
    print(f"   - Has Password: {password_hash is not None}")
    
except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

# Check user status
print(f"\n2️⃣ Checking user status...")
issues = []

if not is_active:
    issues.append("User is not active")
    print("❌ User is not active")
else:
    print("✅ User is active")

if not is_admin:
    issues.append("User is not admin")
    print("⚠️  User is not admin")
else:
    print("✅ User is admin")

if not email_verified:
    issues.append("Email not verified")
    print("⚠️  Email not verified")
else:
    print("✅ Email verified")

if not password_hash:
    issues.append("No password hash")
    print("❌ No password hash set")
else:
    print("✅ Password hash exists")

# Test password verification
print(f"\n3️⃣ Testing password verification...")
if not password_hash:
    print("❌ Cannot test password - no hash stored")
else:
    try:
        # Test password
        password_bytes = TEST_PASSWORD.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        if bcrypt.checkpw(password_bytes, hash_bytes):
            print("✅ Password matches!")
        else:
            print("❌ Password does NOT match")
            issues.append("Password incorrect")
            
            # Generate correct hash for reference
            correct_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            print(f"\n🔧 To set this password, run:")
            print(f"   psql $DATABASE_URL -c \"UPDATE users SET password_hash='{correct_hash}' WHERE email='{TEST_EMAIL}';\"")
            
    except Exception as e:
        print(f"❌ Password verification failed: {e}")
        issues.append(f"Password check error: {e}")

# Summary
print("\n" + "=" * 60)
print("📊 DIAGNOSIS SUMMARY")
print("=" * 60)

if not issues:
    print("✅ All checks passed - login should work!")
else:
    print(f"❌ Found {len(issues)} issue(s):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    print("\n🔧 FIXES:")
    
    if "User is not active" in issues:
        print(f"\n   Fix 1: Activate user")
        print(f"   psql $DATABASE_URL -c \"UPDATE users SET is_active=true WHERE email='{TEST_EMAIL}';\"")
    
    if "User is not admin" in issues:
        print(f"\n   Fix 2: Make user admin")
        print(f"   psql $DATABASE_URL -c \"UPDATE users SET is_admin=true WHERE email='{TEST_EMAIL}';\"")
    
    if "Email not verified" in issues:
        print(f"\n   Fix 3: Verify email")
        print(f"   psql $DATABASE_URL -c \"UPDATE users SET email_verified=true WHERE email='{TEST_EMAIL}';\"")
    
    if "Password incorrect" in issues or "No password hash" in issues:
        print(f"\n   Fix 4: Reset password")
        new_hash = bcrypt.hashpw(TEST_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"   psql $DATABASE_URL -c \"UPDATE users SET password_hash='{new_hash}' WHERE email='{TEST_EMAIL}';\"")
    
    print(f"\n   Or fix all at once:")
    new_hash = bcrypt.hashpw(TEST_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"   psql $DATABASE_URL -c \"UPDATE users SET password_hash='{new_hash}', is_active=true, is_admin=true, email_verified=true WHERE email='{TEST_EMAIL}';\"")

db.close()
print("\n✅ Diagnostic complete")
