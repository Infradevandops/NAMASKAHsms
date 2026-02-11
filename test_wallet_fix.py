#!/usr/bin/env python3
"""Test wallet endpoint after fix."""

import requests
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_wallet():
    print("🧪 Testing Wallet Endpoint Fix\n")
    
    # Step 1: Login
    print("1️⃣ Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@namaskah.app", "password": "Namaskah@Admin2024"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful")
    
    # Step 2: Test API endpoint
    print("\n2️⃣ Testing /api/wallet/balance...")
    headers = {"Authorization": f"Bearer {token}"}
    balance_response = requests.get(f"{BASE_URL}/api/wallet/balance", headers=headers)
    
    if balance_response.status_code != 200:
        print(f"❌ Balance API failed: {balance_response.status_code}")
        print(balance_response.text)
        return False
    
    balance_data = balance_response.json()
    print(f"✅ Balance API works: {balance_data}")
    
    # Step 3: Test wallet page
    print("\n3️⃣ Testing /wallet page...")
    page_response = requests.get(f"{BASE_URL}/wallet", headers=headers)
    
    print(f"   Status Code: {page_response.status_code}")
    
    if page_response.status_code == 200:
        print("✅ Wallet page works!")
        return True
    else:
        print(f"❌ Wallet page failed: {page_response.status_code}")
        print(f"   Response: {page_response.text[:200]}")
        return False

if __name__ == "__main__":
    success = test_wallet()
    sys.exit(0 if success else 1)
