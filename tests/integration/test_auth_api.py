"""Integration tests for authentication API"""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Shared credentials — registered once, reused across tests
_TEST_EMAIL = "integration_auth@test.com"
_TEST_PASSWORD = "SecurePass123!"


def _ensure_test_user():
    """Register the shared test user if not already present."""
    client.post(
        "/api/auth/register",
        json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD, "terms_accepted": True},
    )


def test_register_new_user():
    """Test user registration with a unique email each run"""
    unique_email = f"newuser_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "SecurePass123!",
            "terms_accepted": True,
        },
    )
    assert response.status_code in [200, 201]


def test_login_valid_credentials():
    """Test login with valid credentials"""
    _ensure_test_user()
    response = client.post(
        "/api/auth/login", json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    _ensure_test_user()
    response = client.post(
        "/api/auth/login",
        json={"email": _TEST_EMAIL, "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_get_current_user():
    """Test getting current user profile"""
    _ensure_test_user()
    login_response = client.post(
        "/api/auth/login", json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "email" in data


def test_unauthorized_access():
    """Test accessing protected endpoint without token — app returns 403"""
    response = client.get("/api/auth/me")
    assert response.status_code in [401, 403]
