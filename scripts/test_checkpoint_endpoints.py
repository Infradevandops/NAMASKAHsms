#!/usr/bin/env python3
"""Test checkpoint endpoints with actual API calls."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.user import User
from main import app

client = TestClient(app)


def get_test_user_token():
    """Get a test user and their token."""
    db = SessionLocal()
    try:
        # Try to find an existing test user
        user = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if not user:
            print("  ⚠️  No admin user found")
            return None

        # For testing, we'll use the user_id directly
        # In a real scenario, we'd need to generate a JWT token
        return user.id
    finally:
        db.close()


def test_tier_endpoints():
    """Test tier endpoints."""
    print("\nTesting Tier Endpoints...")

    # Test /api/tiers/
    print("  Testing GET /api/tiers/")
    response = client.get("/api/tiers/")
    print(f"    Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ Response contains: {list(data.keys())}")
        if "tiers" in data:
            print(f"    ✓ Found {len(data['tiers'])} tiers")
    else:
        print(f"    ✗ Error: {response.text}")

    return response.status_code == 200


def test_analytics_endpoints():
    """Test analytics endpoints."""
    print("\nTesting Analytics Endpoints...")

    # Test /api/analytics/summary (requires auth)
    print("  Testing GET /api/analytics/summary")
    response = client.get("/api/analytics/summary")
    print(f"    Status: {response.status_code}")
    if response.status_code in [200, 401, 403]:
        print(f"    ✓ Endpoint exists (status: {response.status_code})")
    else:
        print(f"    ✗ Unexpected status: {response.status_code}")

    return response.status_code in [200, 401, 403]


def test_activity_endpoints():
    """Test activity endpoints."""
    print("\nTesting Activity Endpoints...")

    # Test /api/dashboard/activity/recent (requires auth)
    print("  Testing GET /api/dashboard/activity/recent")
    response = client.get("/api/dashboard/activity/recent")
    print(f"    Status: {response.status_code}")
    if response.status_code in [200, 401, 403]:
        print(f"    ✓ Endpoint exists (status: {response.status_code})")
    else:
        print(f"    ✗ Unexpected status: {response.status_code}")

    return response.status_code in [200, 401, 403]


def test_auth_endpoints():
    """Test auth endpoints."""
    print("\nTesting Auth Endpoints...")

    # Test /api/auth/me (requires auth)
    print("  Testing GET /api/auth/me")
    response = client.get("/api/auth/me")
    print(f"    Status: {response.status_code}")
    if response.status_code in [200, 401, 403]:
        print(f"    ✓ Endpoint exists (status: {response.status_code})")
    else:
        print(f"    ✗ Unexpected status: {response.status_code}")

    return response.status_code in [200, 401, 403]


def test_settings_endpoints():
    """Test settings endpoints."""
    print("\nTesting Settings Endpoints...")

    # Test /api/user/settings (requires auth)
    print("  Testing GET /api/user/settings")
    response = client.get("/api/user/settings")
    print(f"    Status: {response.status_code}")
    if response.status_code in [200, 401, 403]:
        print(f"    ✓ Endpoint exists (status: {response.status_code})")
    else:
        print(f"    ✗ Unexpected status: {response.status_code}")

    return response.status_code in [200, 401, 403]


def test_api_key_endpoints():
    """Test API key endpoints."""
    print("\nTesting API Key Endpoints...")

    # Test /api/keys (requires auth)
    print("  Testing GET /api/keys")
    response = client.get("/api/keys")
    print(f"    Status: {response.status_code}")
    if response.status_code in [200, 401, 403]:
        print(f"    ✓ Endpoint exists (status: {response.status_code})")
    else:
        print(f"    ✗ Unexpected status: {response.status_code}")

    return response.status_code in [200, 401, 403]


def main():
    """Run all endpoint tests."""
    print("=" * 60)
    print("CHECKPOINT ENDPOINT TESTS")
    print("=" * 60)

    results = []

    # Test endpoints
    results.append(("Tier Endpoints", test_tier_endpoints()))
    results.append(("Analytics Endpoints", test_analytics_endpoints()))
    results.append(("Activity Endpoints", test_activity_endpoints()))
    results.append(("Auth Endpoints", test_auth_endpoints()))
    results.append(("Settings Endpoints", test_settings_endpoints()))
    results.append(("API Key Endpoints", test_api_key_endpoints()))

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All endpoint tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
