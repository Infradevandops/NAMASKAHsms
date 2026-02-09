"""Integration tests for wallet/billing API"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    """Get authentication token"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    return response.json()["access_token"]

def test_get_balance(auth_token):
    """Test getting user balance"""
    response = client.get("/api/billing/balance", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data or "credits" in data

def test_get_transaction_history(auth_token):
    """Test getting transaction history"""
    response = client.get("/api/billing/history", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))

def test_initialize_payment(auth_token):
    """Test payment initialization"""
    response = client.post("/api/billing/initialize-payment", 
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"amount_usd": 10.0}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "authorization_url" in data or "reference" in data

def test_get_balance_unauthorized():
    """Test balance endpoint without auth"""
    response = client.get("/api/billing/balance")
    assert response.status_code == 401
