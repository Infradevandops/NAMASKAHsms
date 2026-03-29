"""E2E test configuration and fixtures."""

import os
import pytest


@pytest.fixture(scope="session")
def base_url():
    """Base URL for E2E tests."""
    return os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture
def test_user():
    """Test user credentials."""
    return {
        "email": os.getenv("TEST_USER_EMAIL", "admin@namaskah.app"),
        "password": os.getenv("TEST_USER_PASSWORD", "test-password-123"),
    }


@pytest.fixture
def test_timeout():
    """Test timeout in milliseconds."""
    return int(os.getenv("TEST_TIMEOUT", "30000"))
