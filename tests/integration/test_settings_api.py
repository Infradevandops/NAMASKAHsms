"""Integration tests for settings and notifications API"""
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

def test_get_notifications(auth_token):
    """Test getting notifications"""
    response = client.get("/api/notifications", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200

def test_get_webhooks(auth_token):
    """Test getting webhooks"""
    response = client.get("/api/webhooks", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200

def test_get_referral_stats(auth_token):
    """Test getting referral stats"""
    response = client.get("/api/referrals/stats", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200

def test_get_current_tier(auth_token):
    """Test getting current tier"""
    response = client.get("/api/tiers/current", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "current_tier" in data or "tier" in data
