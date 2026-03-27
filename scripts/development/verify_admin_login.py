#!/usr/bin/env python3
"""Verify admin login credentials work correctly."""

import sys
import os
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/namaskah")

# Default admin credentials
ADMIN_EMAIL = "admin@namaskah.app"
ADMIN_PASSWORD = "<admin-password>"

print("🔐 Admin Login Verification")
print("=" * 60)

# Connect to database
try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    print("✅ Database connected")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Check admin user
print(f"\n📧 Checking: {ADMIN_EMAIL}")
try:
    result = db.execute(
        text("SELECT id, email, password_hash, is_admin, is_active FROM users WHERE email = :email"),
        {"email": ADMIN_EMAIL}
    ).fetchone()
    
    if not result:
        print(f"❌ Admin user not found")
        print(f"\n🔧 Create admin user:")
        print(f"   python3 scripts/create_admin_user.py")
        sys.exit(1)
    
    user_id, email, password_hash, is_admin, is_active = result
    print(f"✅ User exists: {user_id}")
    
except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

# Verify status
print(f"\n🔍 Status Checks:")
checks_passed = 0
checks_total = 3

if is_active:
    print("✅ User is active")
    checks_passed += 1
else:
    print("❌ User is NOT active")

if is_admin:
    print("✅ User is admin")
    checks_passed += 1
else:
    print("❌ User is NOT admin")

if password_hash:
    print("✅ Password hash exists")
    checks_passed += 1
else:
    print("❌ No password hash")

# Test password
print(f"\n🔑 Password Verification:")
if not password_hash:
    print("❌ Cannot verify - no password hash")
else:
    try:
        password_bytes = ADMIN_PASSWORD.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        if bcrypt.checkpw(password_bytes, hash_bytes):
            print("✅ Password matches!")
            checks_passed += 1
            checks_total += 1
        else:
            print("❌ Password does NOT match")
            print(f"\n🔧 Reset password:")
            new_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            print(f"   psql $DATABASE_URL -c \"UPDATE users SET password_hash='{new_hash}' WHERE email='{ADMIN_EMAIL}';\"")
            
    except Exception as e:
        print(f"❌ Password check failed: {e}")

# Summary
print("\n" + "=" * 60)
print(f"📊 RESULT: {checks_passed}/{checks_total} checks passed")
print("=" * 60)

if checks_passed == checks_total:
    print("✅ SUCCESS - Admin login should work!")
    print(f"\n🎯 Test login:")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"   URL: http://localhost:8000/login")
    sys.exit(0)
else:
    print("❌ FAILED - Issues found")
    print(f"\n🔧 Fix all issues:")
    new_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"   psql $DATABASE_URL -c \"UPDATE users SET password_hash='{new_hash}', is_active=true, is_admin=true WHERE email='{ADMIN_EMAIL}';\"")
    sys.exit(1)

db.close()
