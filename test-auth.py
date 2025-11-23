#!/usr/bin/env python3
"""
Quick auth test script for Docker debugging
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_auth():
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Namaskah Auth...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Try login
    login_data = {
        "email": os.getenv('TEST_EMAIL', 'admin@namaskah.app'),
        "password": os.getenv('TEST_PASSWORD')
    }
    
    if not login_data['password']:
        print("❌ TEST_PASSWORD not set in .env")
        return
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"🔐 Login attempt: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Login successful!")
                return data["access_token"]
            else:
                print("❌ No token in response")
        else:
            print(f"❌ Login failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Test 3: Check database
    try:
        response = requests.get(f"{base_url}/api/countries/")
        print(f"🌍 Countries API: {response.status_code}")
    except Exception as e:
        print(f"❌ Countries API error: {e}")

if __name__ == "__main__":
    test_auth()