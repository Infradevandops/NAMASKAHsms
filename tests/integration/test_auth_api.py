"""Integration tests for authentication API"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_new_user():
    """Test user registration"""
    response = client.post("/api/auth/register", json={
        "email": "newuser@test.com",
        "password": "SecurePass123!"
    })
    assert response.status_code in [200, 201, 409]  # 409 if user exists

def test_login_valid_credentials():
    """Test login with valid credentials"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_current_user():
    """Test getting current user profile"""
    # Login first
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Get profile
    response = client.get("/api/v1/user/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "email" in data

def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401
