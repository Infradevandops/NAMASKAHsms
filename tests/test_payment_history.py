"""Tests for Payment History and Refund endpoints."""


import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():

    return TestClient(app)


def test_payment_history_requires_auth(client):

    """Payment history should require authentication."""
    response = client.get("/api/billing/history")
    assert response.status_code == 401


def test_payment_history_returns_list(client, auth_headers):

    """Payment history should return list of payments."""
    response = client.get("/api/billing/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data or isinstance(data, list)


def test_payment_history_pagination(client, auth_headers):

    """Payment history should support pagination."""
    response = client.get("/api/billing/history?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200


def test_payment_history_filter_by_status(client, auth_headers):

    """Payment history should support status filter."""
    response = client.get("/api/billing/history?status=completed", headers=auth_headers)
    assert response.status_code == 200


def test_refund_request_requires_auth(client):

    """Refund request should require authentication."""
    response = client.post(
        "/api/billing/refund",
        json={"payment_id": "test_payment", "reason": "Test reason"},
    )
    assert response.status_code == 401


def test_refund_request_requires_payment_id(client, auth_headers):

    """Refund request should require payment_id."""
    response = client.post("/api/billing/refund", json={"reason": "Test reason"}, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_refund_request_requires_reason(client, auth_headers):

    """Refund request should require reason."""
    response = client.post("/api/billing/refund", json={"payment_id": "test_payment"}, headers=auth_headers)
    assert response.status_code in [400, 422]


def test_refund_list_requires_auth(client):

    """Refund list should require authentication."""
    response = client.get("/api/billing/refunds")
    assert response.status_code == 401


def test_refund_list_returns_data(client, auth_headers):

    """Refund list should return refund data."""
    response = client.get("/api/billing/refunds", headers=auth_headers)
    assert response.status_code == 200


def test_refund_status_check(client, auth_headers):

    """Should be able to check refund status."""
    response = client.get("/api/billing/refund/fake-reference", headers=auth_headers)
    # Will 404 without real refund, but endpoint should exist and return 404, not 500
    assert response.status_code in [200, 404]


def test_refund_invalid_payment_id(client, auth_headers):

    """Should reject refund for invalid payment ID."""
    response = client.post(
        "/api/billing/refund",
        json={"payment_id": "nonexistent_payment_12345", "reason": "Test reason"},
        headers=auth_headers,
    )
    assert response.status_code in [400, 404, 422]
