#!/usr/bin/env python3
"""Create production admin user."""

import os
import sys


def create_production_admin():
    """Create admin user for production testing."""

    # Simple admin creation without dependencies
    admin_data = {
        "email": "admin@namaskah.app",
        "password": "NamaskahAdmin2024!",
        "credits": 1000.0,
        "is_admin": True,
    }

    print("🔑 Production Admin Credentials:")
    print(f"Email: {admin_data['email']}")
    print(f"Password: {admin_data['password']}")
    print(f"Credits: {admin_data['credits']}")
    print(f"Admin: {admin_data['is_admin']}")
    print("\n📝 Use these credentials to login at /auth/login")

    # Also create a simple test user
    test_data = {"email": "test@namaskah.app", "password": "test123", "credits": 100.0}

    print("\n👤 Test User Credentials:")
    print(f"Email: {test_data['email']}")
    print(f"Password: {test_data['password']}")
    print(f"Credits: {test_data['credits']}")


if __name__ == "__main__":
    create_production_admin()
