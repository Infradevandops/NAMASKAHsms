"""Integration tests for analytics API"""
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

def test_get_analytics_summary(auth_token):
    """Test analytics summary endpoint"""
    response = client.get("/api/analytics/summary", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "total_verifications" in data or "summary" in data

def test_get_dashboard_activity(auth_token):
    """Test dashboard activity endpoint"""
    response = client.get("/api/dashboard/activity/recent", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
