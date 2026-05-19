"""Tests for authentication endpoints."""

import uuid

import bcrypt


class TestAuthentication:
    def test_register_success(self, client, db):
        """Registration returns a token."""
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
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email

    def test_register_duplicate_email(self, client, regular_user):
        """Registration with existing email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "regular@example.com",
                "password": "SecurePass123!",
                "terms_accepted": True,
            },
        )
        assert response.status_code == 400

    def test_register_missing_terms(self, client):
        """Registration without terms_accepted fails."""
        unique_email = f"terms_{uuid.uuid4().hex[:8]}@test.com"
        response = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "terms_accepted": False,
            },
        )
        assert response.status_code == 400

    def test_login_success(self, client, db):
        """Login with valid credentials returns token."""
        # Register a fresh user with a known real password
        email = f"login_{uuid.uuid4().hex[:8]}@test.com"
        password = "LoginPass123!"
        client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "terms_accepted": True},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == email

    def test_login_wrong_password(self, client, db):
        """Login with wrong password returns 401."""
        email = f"wrongpw_{uuid.uuid4().hex[:8]}@test.com"
        client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "CorrectPass123!",
                "terms_accepted": True,
            },
        )
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPass123!"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Login with unknown email returns 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@nowhere.com", "password": "Pass123!"},
        )
        assert response.status_code == 401
