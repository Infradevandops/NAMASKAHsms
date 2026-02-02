#!/usr/bin/env python3
"""
import requests

Quick diagnostic script to test notification and transaction endpoints
"""


def test_endpoints():

    """Test notification and transaction endpoints"""

    # You'll need to replace this with a valid token from your browser
    # Go to browser dev tools -> Application -> Local Storage -> access_token
    token = input("Enter your access_token from browser localStorage: ").strip()

if not token:
        print("❌ No token provided")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    base_url = "https://namaskah.app"  # Change if testing locally

    print(f"🔍 Testing endpoints on {base_url}")
    print("=" * 50)

    # Test 1: Notifications endpoint
    print("1️⃣ Testing notifications endpoint...")
try:
        response = requests.get(f"{base_url}/api/notifications", headers=headers)
        print(f"   Status: {response.status_code}")

if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            unread_count = data.get('unread_count', 0)
            print(f"   ✅ Found {len(notifications)} notifications ({unread_count} unread)")

if notifications:
                latest = notifications[0]
                print(f"   📱 Latest: {latest.get('title', 'No title')} - {latest.get('message', 'No message')}")
else:
            print(f"   ❌ Error: {response.text}")
except Exception as e:
        print(f"   ❌ Exception: {e}")

    print()

    # Test 2: Verification history endpoint
    print("2️⃣ Testing verification history endpoint...")
try:
        response = requests.get(f"{base_url}/api/v1/verify/history", headers=headers)
        print(f"   Status: {response.status_code}")

if response.status_code == 200:
            data = response.json()
            verifications = data.get('verifications', [])
            total_count = data.get('total_count', 0)
            print(f"   ✅ Found {len(verifications)} verifications (total: {total_count})")

if verifications:
                latest = verifications[0]
                print(f"   📱 Latest: {latest.get('service_name')} - {latest.get('status')} - ${latest.get('cost', 0):.2f}")
else:
            print(f"   ❌ Error: {response.text}")
except Exception as e:
        print(f"   ❌ Exception: {e}")

    print()

    # Test 3: Create test notification
    print("3️⃣ Testing notification creation...")
try:
        # This would need to be done server-side, but we can check if the endpoint exists
        response = requests.get(f"{base_url}/api/notifications", headers=headers)
if response.status_code == 200:
            print("   ✅ Notification endpoint is accessible")
else:
            print(f"   ❌ Cannot access notifications: {response.status_code}")
except Exception as e:
        print(f"   ❌ Exception: {e}")

    print()
    print("🔧 Quick Fixes:")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify access_token is valid in localStorage")
    print("3. Check if notification bell has onclick handler")
    print("4. Verify API endpoints are returning data")

if __name__ == "__main__":
    test_endpoints()