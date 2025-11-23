"""Test error handling in API endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestAuthErrorHandling:
    """Test authentication endpoint error handling."""

    def test_register_invalid_json(self, client):
        """Test registration with invalid JSON."""
        response = client.post("/api/auth/register", content="invalid json")
        assert response.status_code == 400

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        response = client.post("/api/auth/register", json={"password": "test123"})
        assert response.status_code == 422

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "123"
        })
        assert response.status_code == 422


class TestBillingErrorHandling:
    """Test billing endpoint error handling."""

    def test_add_credits_no_auth(self, client):
        """Test add credits without authentication."""
        response = client.post("/api/billing/add-credits", json={"amount": 50})
        assert response.status_code == 401

    def test_add_credits_invalid_json(self, client):
        """Test add credits with invalid JSON."""
        response = client.post(
            "/api/billing/add-credits",
            content="invalid json",
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 400


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCountriesEndpoint:
    """Test countries endpoint."""

    def test_get_countries(self, client):
        """Test getting countries list."""
        response = client.get("/api/countries/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "countries" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
