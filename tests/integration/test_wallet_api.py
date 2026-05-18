"""Integration tests for wallet/billing API"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Register and login to get token"""
    import uuid

    email = f"wallet_{uuid.uuid4().hex[:8]}@test.com"
    password = "WalletTest123!"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "terms_accepted": True},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]


def test_get_balance(auth_token):
    """Test getting user balance"""
    response = client.get(
        "/api/billing/balance", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data or "credits" in data


def test_get_transaction_history(auth_token):
    """Test getting transaction history"""
    response = client.get(
        "/api/wallet/history", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


def test_initialize_payment(auth_token):
    """Test payment initialization — mock Paystack to avoid real API calls"""
    mock_response = {
        "authorization_url": "https://checkout.paystack.com/mock",
        "reference": "mock_ref_123",
        "payment_id": "mock_payment_id",
        "access_code": "mock_access_code",
    }
    with patch(
        "app.services.payment_service.PaymentService.initialize_payment",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.post(
            "/api/wallet/paystack/initialize",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": 10.0},
        )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "authorization_url" in data or "reference" in data


def test_get_balance_unauthorized():
    """Test balance endpoint without auth"""
    response = client.get("/api/billing/balance")
    assert response.status_code in [401, 403]
