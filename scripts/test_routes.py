#!/usr/bin/env python3
"""
Route Testing Script for Namaskah SMS
Tests all public routes to ensure they're working correctly
"""

import sys
from typing import List, Tuple

import requests


def test_route(base_url: str, path: str, expected_status: int = 200) -> Tuple[bool, str, int]:
    """Test a single route and return result."""
    url = f"{base_url}{path}"
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=10)
        success = response.status_code == expected_status

        if success:
            return True, f"✅ {path} - OK ({response.status_code})", response.status_code
        else:
            return False, f"❌ {path} - FAIL ({response.status_code})", response.status_code

    except requests.exceptions.RequestException as e:
        return False, f"❌ {path} - ERROR: {str(e)}", 0


def test_all_routes(base_url: str) -> None:
    """Test all public routes."""

    print(f"🔍 Testing routes for: {base_url}")
    print("=" * 60)

    # Public routes that should work without authentication
    public_routes = [
        "/",                    # Landing page
        "/app",                 # Dashboard
        "/services",            # Services page
        "/pricing",             # Pricing page
        "/about",               # About page
        "/contact",             # Contact page
        "/system/health",       # Health check
        "/docs",                # API documentation
        "/redoc",               # Alternative docs
    ]

    # API routes that should return 401 (unauthorized) but not 404
    api_routes = [
        "/auth/me",             # Should return 401
        "/verify/history",      # Should return 401
        "/wallet/balance",      # Should return 401
        "/admin/stats",         # Should return 401 or 403
    ]

    passed = 0
    total = 0

    print("📱 Testing Public Routes (should return 200):")
    print("-" * 40)

    for route in public_routes:
        success, message, status_code = test_route(base_url, route, 200)
        print(message)
        if success:
            passed += 1
        total += 1

    print("\n🔐 Testing Protected Routes (should return 401, not 404):")
    print("-" * 40)

    for route in api_routes:
        success, message, status_code = test_route(base_url, route, 401)
        # Accept both 401 (unauthorized) and 403 (forbidden) as success
        if status_code in [401, 403]:
            print(f"✅ {route} - OK ({status_code}) - Properly protected")
            passed += 1
        elif status_code == 404:
            print(f"❌ {route} - FAIL (404) - Route not found!")
        else:
            print(f"⚠️ {route} - UNEXPECTED ({status_code})")
        total += 1

    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} routes working correctly")

    if passed == total:
        print("🎉 All routes are working correctly!")
        return True
    else:
        print(f"⚠️ {total - passed} routes have issues")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        # Default to production URL
        base_url = "https://namaskahsms.onrender.com"

    print("🚀 Namaskah SMS Route Tester")
    print("=" * 60)

    success = test_all_routes(base_url)

    if not success:
        print("\n🔧 Troubleshooting Tips:")
        print("- Check if the application is deployed and running")
        print("- Verify middleware configurations")
        print("- Check router inclusion in main.py")
        print("- Review exclude_paths in JWT middleware")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
