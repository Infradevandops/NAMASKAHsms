#!/usr/bin/env python3
"""
Test script to verify the /api/auth/me endpoint works correctly
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login_and_get_user():
    """Test login and then fetch user data"""
    
    # Step 1: Login with admin user
    print("Step 1: Logging in...")
    login_data = {
        "email": "admin@namaskah.app",
        "password": "Namaskah@Admin2024"  # From .env
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful!")
            print(f"Token (first 20 chars): {token[:20]}...")
            
            # Step 2: Get user data
            print("\nStep 2: Fetching user data...")
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            
            print(f"User API Status: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                print(f"✅ User data retrieved successfully!")
                print(f"\nUser Data:")
                print(f"  ID: {user_data.get('id')}")
                print(f"  Email: {user_data.get('email')}")
                print(f"  Created: {user_data.get('created_at')}")
                print(f"  Credits: {user_data.get('credits')}")
                print(f"  Admin: {user_data.get('is_admin')}")
                
                print(f"\n✅ API is working correctly!")
                print(f"\nTo test in browser:")
                print(f"1. Open http://127.0.0.1:8000/auth/login")
                print(f"2. Login with: admin@namaskah.app / admin123")
                print(f"3. Go to http://127.0.0.1:8000/settings")
                print(f"4. Open DevTools (F12) and check Console")
                
                return True
            else:
                print(f"❌ Failed to get user data: {user_response.text}")
                return False
        else:
            print(f"❌ Login failed: {response.text}")
            print(f"\nTrying to check if admin user exists...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print(f"Make sure the server is running: ./start-fast.sh")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Settings Page API Endpoint")
    print("=" * 60)
    print()
    
    success = test_login_and_get_user()
    
    print()
    print("=" * 60)
    if success:
        print("✅ TEST PASSED - API is working!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("=" * 60)
