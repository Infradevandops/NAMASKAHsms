"""Tests for authentication endpoints."""


class TestAuthentication:

    def test_register_success(self, client, db):

        response = client.post(
            "/api/auth/register",
            json={"email": "newuser@test.com", "password": "SecurePass123!"},
        )
        if response.status_code != 201:
            print(f"Auth Register Failed: {response.status_code} - {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@test.com"

    def test_register_duplicate_email(self, client, regular_user):

        """Test registration with existing email fails."""
        response = client.post(
            "/api/auth/register",
            json={"email": "user@test.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 400

    def test_login_success(self, client, regular_user):

        """Test login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "user@test.com"

    def test_login_wrong_password(self, client, regular_user):

        """Test login with invalid password."""
        response = client.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401