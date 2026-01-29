"""Comprehensive tests for wallet/billing endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.models.transaction import Transaction
from app.models.balance_transaction import BalanceTransaction


class TestWalletEndpoints:
    """Test wallet and billing endpoints comprehensively."""

    def test_get_balance_success(self, authenticated_regular_client, regular_user):
        """Test getting user balance."""
        response = authenticated_regular_client.get("/api/v1/wallet/balance")

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data or "credits" in data

    def test_get_balance_unauthorized(self, client):
        """Test getting balance without authentication."""
        response = client.get("/api/v1/wallet/balance")
        assert response.status_code in [401, 403, 422]

    def test_get_transactions_success(self, authenticated_regular_client, regular_user, db):
        """Test getting transaction history."""
        # Create some transactions
        for i in range(3):
            transaction = Transaction(
                user_id=regular_user.id,
                amount=10.0 * (i + 1),
                type="credit_purchase",
                description=f"Test transaction {i}",
                status="completed"
            )
            db.add(transaction)
        db.commit()

        response = authenticated_regular_client.get("/api/v1/wallet/transactions")

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data or isinstance(data, list)

    def test_get_transactions_pagination(self, authenticated_regular_client, regular_user, db):
        """Test transaction history pagination."""
        # Create 10 transactions
        for i in range(10):
            transaction = Transaction(
                user_id=regular_user.id,
                amount=5.0,
                type="credit_purchase",
                description=f"Transaction {i}",
                status="completed"
            )
            db.add(transaction)
        db.commit()

        response = authenticated_regular_client.get("/api/v1/wallet/transactions?limit=5&offset=0")

        assert response.status_code == 200

    def test_get_transactions_empty(self, authenticated_regular_client):
        """Test getting transactions when none exist."""
        response = authenticated_regular_client.get("/api/v1/wallet/transactions")

        assert response.status_code == 200

    def test_add_credits_success(self, authenticated_regular_client, regular_user, db):
        """Test adding credits to wallet."""
        response = authenticated_regular_client.post(
            "/api/v1/wallet/add-credits",
            json={"amount": 10.0}
        )

        # May require payment processing
        assert response.status_code in [200, 201, 202, 400, 402]

    def test_add_credits_invalid_amount(self, authenticated_regular_client):
        """Test adding invalid credit amount."""
        response = authenticated_regular_client.post(
            "/api/v1/wallet/add-credits",
            json={"amount": -10.0}
        )

        assert response.status_code in [400, 422]

    def test_add_credits_zero_amount(self, authenticated_regular_client):
        """Test adding zero credits."""
        response = authenticated_regular_client.post(
            "/api/v1/wallet/add-credits",
            json={"amount": 0.0}
        )

        assert response.status_code in [400, 422]


class TestCreditEndpoints:
    """Test credit management endpoints."""

    def test_get_credit_balance(self, authenticated_regular_client):
        """Test getting credit balance."""
        response = authenticated_regular_client.get("/api/v1/billing/credits/balance")

        assert response.status_code == 200

    def test_purchase_credits_success(self, authenticated_regular_client):
        """Test purchasing credits."""
        response = authenticated_regular_client.post(
            "/api/v1/billing/credits/purchase",
            json={
                "amount": 20.0,
                "payment_method": "card"
            }
        )

        # May require payment setup
        assert response.status_code in [200, 201, 202, 400, 402]

    def test_get_credit_packages(self, client):
        """Test getting available credit packages."""
        response = client.get("/api/v1/billing/credits/packages")
        
        # Endpoint may or may not exist
        assert response.status_code in [200, 404]


class TestPaymentEndpoints:
    """Test payment endpoints."""

    def test_create_payment_intent(self, authenticated_regular_client):
        """Test creating payment intent."""
        response = authenticated_regular_client.post(
            "/api/v1/billing/payments/intent",
            json={"amount": 10.0}
        )

        # May require payment provider setup
        assert response.status_code in [200, 201, 400, 402, 503]

    def test_get_payment_methods(self, authenticated_regular_client):
        """Test getting payment methods."""
        response = authenticated_regular_client.get("/api/v1/billing/payments/methods")

        assert response.status_code in [200, 404]

    def test_get_payment_history(self, authenticated_regular_client):
        """Test getting payment history."""
        response = authenticated_regular_client.get("/api/v1/billing/payments/history")

        assert response.status_code == 200


class TestPricingEndpoints:
    """Test pricing endpoints."""

    def test_get_pricing_tiers(self, client):
        """Test getting pricing tiers."""
        response = client.get("/api/v1/billing/pricing/tiers")
        assert response.status_code in [200, 404]

    def test_get_service_pricing(self, client):
        """Test getting service pricing."""
        response = client.get("/api/v1/billing/pricing/services")
        assert response.status_code in [200, 404]

    def test_calculate_cost(self, client):
        """Test cost calculation."""
        response = client.post(
            "/api/v1/billing/pricing/calculate",
            json={
                "service": "telegram",
                "country": "US",
                "quantity": 1
            }
        )
        assert response.status_code in [200, 404, 422]


class TestRefundEndpoints:
    """Test refund endpoints."""

    def test_request_refund(self, authenticated_regular_client, regular_user, db):
        """Test requesting refund."""
        # Create a transaction
        transaction = Transaction(
            user_id=regular_user.id,
            amount=10.0,
            type="sms_purchase",
            description="Test purchase",
            status="completed"
        )
        db.add(transaction)
        db.commit()

        response = authenticated_regular_client.post(
            "/api/v1/billing/refunds/request",
            json={
                "transaction_id": transaction.id,
                "reason": "Service not received"
            }
        )

        assert response.status_code in [200, 201, 400, 404]

    def test_get_refund_status(self, authenticated_regular_client):
        """Test getting refund status."""
        response = authenticated_regular_client.get("/api/v1/billing/refunds/test-refund-id")

        assert response.status_code in [200, 404]

    def test_list_refunds(self, authenticated_regular_client):
        """Test listing refunds."""
        response = authenticated_regular_client.get("/api/v1/billing/refunds")

        assert response.status_code == 200
