#!/usr/bin/env python3
"""Test admin login via API endpoint."""

import requests
import sys

BASE_URL = "http://localhost:9876"
ADMIN_EMAIL = "admin@namaskah.app"
ADMIN_PASSWORD = "Namaskah@Admin2024"

print("🧪 Testing Admin Login API")
print("=" * 60)

# Test login endpoint
print(f"\n1️⃣ POST /api/auth/login")
try:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Login successful!")
        print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"   Type: {data.get('token_type', 'N/A')}")
        
        # Save token for next test
        token = data.get('access_token')
        
    else:
        print(f"   ❌ Login failed: {response.text}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print(f"   ❌ Server not running at {BASE_URL}")
    print(f"\n   Start server:")
    print(f"   uvicorn main:app --host 127.0.0.1 --port 8000")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    sys.exit(1)

# Test /me endpoint
print(f"\n2️⃣ GET /api/auth/me")
try:
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ User info retrieved!")
        print(f"   ID: {data.get('id', 'N/A')}")
        print(f"   Email: {data.get('email', 'N/A')}")
        print(f"   Tier: {data.get('tier', 'N/A')}")
        print(f"   Credits: ${data.get('credits', 0):.2f}")
    else:
        print(f"   ❌ Failed: {response.text}")
        
except Exception as e:
    print(f"   ❌ Request failed: {e}")

# Test admin endpoint
print(f"\n3️⃣ GET /api/admin/stats")
try:
    response = requests.get(
        f"{BASE_URL}/api/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ✅ Admin access confirmed!")
    elif response.status_code == 403:
        print(f"   ❌ Admin access denied")
    else:
        print(f"   ⚠️  Endpoint response: {response.status_code}")
        
except Exception as e:
    print(f"   ⚠️  Request failed: {e}")

# Summary
print("\n" + "=" * 60)
print("✅ Admin login verification complete!")
print("=" * 60)
print(f"\n🎯 Credentials:")
print(f"   Email: {ADMIN_EMAIL}")
print(f"   Password: {ADMIN_PASSWORD}")
print(f"\n🌐 Test in browser:")
print(f"   {BASE_URL}/login")
