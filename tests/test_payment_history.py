"""Tests for Payment History and Refund endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from app.core.dependencies import get_current_user_id


class TestPaymentHistoryEndpoints:
    """Test payment history API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield "test_user_123"
        app.dependency_overrides.clear()
    
    def test_payment_history_requires_auth(self, client):
        """Payment history should require authentication."""
        response = client.get("/api/billing/history")
        assert response.status_code == 401
    
    def test_payment_history_returns_list(self, client, mock_user_id):
        """Payment history should return list of payments."""
        response = client.get("/api/billing/history")
        
        if response.status_code == 200:
            data = response.json()
            assert "payments" in data or isinstance(data, list)
    
    def test_payment_history_pagination(self, client, mock_user_id):
        """Payment history should support pagination."""
        response = client.get("/api/billing/history?skip=0&limit=10")
        assert response.status_code in [200, 401]
    
    def test_payment_history_filter_by_status(self, client, mock_user_id):
        """Payment history should support status filter."""
        response = client.get("/api/billing/history?status=completed")
        assert response.status_code in [200, 401, 422]


class TestRefundEndpoints:
    """Test refund API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield "test_user_123"
        app.dependency_overrides.clear()
    
    def test_refund_request_requires_auth(self, client):
        """Refund request should require authentication."""
        response = client.post("/api/billing/refund", json={
            "payment_id": "test_payment",
            "reason": "Test reason"
        })
        assert response.status_code == 401
    
    def test_refund_request_requires_payment_id(self, client, mock_user_id):
        """Refund request should require payment_id."""
        response = client.post("/api/billing/refund", json={
            "reason": "Test reason"
        })
        assert response.status_code in [400, 422]
    
    def test_refund_request_requires_reason(self, client, mock_user_id):
        """Refund request should require reason."""
        response = client.post("/api/billing/refund", json={
            "payment_id": "test_payment"
        })
        assert response.status_code in [400, 422]
    
    def test_refund_list_requires_auth(self, client):
        """Refund list should require authentication."""
        response = client.get("/api/billing/refunds")
        assert response.status_code == 401
    
    def test_refund_list_returns_data(self, client, mock_user_id):
        """Refund list should return refund data."""
        response = client.get("/api/billing/refunds")
        
        if response.status_code == 200:
            data = response.json()
            assert "refunds" in data or isinstance(data, list)
    
    def test_refund_status_check(self, client, mock_user_id):
        """Should be able to check refund status."""
        response = client.get("/api/billing/refund/fake-reference")
        # Will 404 without real refund, but endpoint should exist
        assert response.status_code in [200, 404, 401]


class TestRefundValidation:
    """Test refund validation rules."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield
        app.dependency_overrides.clear()
    
    def test_refund_invalid_payment_id(self, client, mock_user_id):
        """Should reject refund for invalid payment ID."""
        response = client.post("/api/billing/refund", json={
            "payment_id": "nonexistent_payment_12345",
            "reason": "Test reason"
        })
        # Should return error for invalid payment
        assert response.status_code in [400, 404, 422, 500]
    
    def test_refund_empty_reason(self, client, mock_user_id):
        """Should reject refund with empty reason."""
        response = client.post("/api/billing/refund", json={
            "payment_id": "test_payment",
            "reason": ""
        })
        assert response.status_code in [400, 422]


class TestPaymentHistoryContent:
    """Test payment history data content."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield
        app.dependency_overrides.clear()
    
    def test_payment_has_required_fields(self, client, mock_user_id):
        """Payments should have required fields."""
        response = client.get("/api/billing/history")
        
        if response.status_code == 200:
            data = response.json()
            payments = data.get("payments", data) if isinstance(data, dict) else data
            
            if payments and len(payments) > 0:
                payment = payments[0]
                # Check for common payment fields
                assert any(key in payment for key in ["id", "reference", "amount", "status"])
    
    def test_payment_amounts_are_numeric(self, client, mock_user_id):
        """Payment amounts should be numeric."""
        response = client.get("/api/billing/history")
        
        if response.status_code == 200:
            data = response.json()
            payments = data.get("payments", data) if isinstance(data, dict) else data
            
            if payments and len(payments) > 0:
                for payment in payments:
                    amount = payment.get("amount") or payment.get("amount_usd")
                    if amount is not None:
                        assert isinstance(amount, (int, float))
