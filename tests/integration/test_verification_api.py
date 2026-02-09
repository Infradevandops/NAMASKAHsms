"""Integration tests for verification API"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    return response.json()["access_token"]

def test_get_verification_history(auth_token):
    """Test getting verification history"""
    response = client.get("/api/v1/verify/history", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "verifications" in data or isinstance(data, list)

def test_get_services(auth_token):
    """Test getting available services"""
    response = client.get("/api/services", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200

def test_get_countries(auth_token):
    """Test getting available countries"""
    response = client.get("/api/countries", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
