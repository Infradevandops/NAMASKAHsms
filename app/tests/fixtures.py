"""Secure test fixtures and utilities."""
import secrets
import string
from typing import Dict


def generate_test_password(length: int = 12) -> str:
    """Generate secure random password for tests."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_test_api_key() -> str:
    """Generate test API key."""
    return f"test_{secrets.token_urlsafe(32)}"


def get_test_credentials() -> Dict[str, str]:
    """Get test credentials (generated per test run)."""
    return {
        "user_password": generate_test_password(),
        "admin_password": generate_test_password(),
        "api_key": generate_test_api_key(),
    }


# Generate credentials once per test session
TEST_CREDENTIALS = get_test_credentials()
