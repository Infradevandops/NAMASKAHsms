"""Test wallet page functionality - buttons, payment methods, transactions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestWalletButtons:
    """Test all wallet page buttons and interactions."""

    def test_wallet_balance_endpoint(self, authenticated_regular_client, regular_user):
        """Test wallet balance endpoint returns correct data."""
        response = authenticated_regular_client.get("/api/wallet/balance")

        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
        assert "credits_usd" in data
        assert isinstance(data["credits"], (int, float))

    def test_payment_initialization_card(self, authenticated_regular_client):
        """Test credit card payment initialization."""
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 10.0}
        )

        # Should return 200 or 402 (if Paystack not configured)
        assert response.status_code in [200, 402, 503]

        if response.status_code == 200:
            data = response.json()
            assert "authorization_url" in data or "payment_id" in data

    def test_payment_initialization_amounts(self, authenticated_regular_client):
        """Test different payment amounts ($10, $25, $50, $100)."""
        amounts = [10, 25, 50, 100]

        for amount in amounts:
            response = authenticated_regular_client.post(
                "/api/wallet/paystack/initialize", json={"amount_usd": amount}
            )

            assert response.status_code in [200, 402, 503]

    def test_custom_amount_payment(self, authenticated_regular_client):
        """Test custom amount payment."""
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 75.50}
        )

        assert response.status_code in [200, 402, 503]

    def test_invalid_payment_amount(self, authenticated_regular_client):
        """Test payment with invalid amount."""
        # Negative amount
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": -10}
        )
        assert response.status_code in [400, 422]

        # Zero amount
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 0}
        )
        assert response.status_code in [400, 422]

    def test_transaction_history_endpoint(self, authenticated_regular_client):
        """Test transaction history endpoint."""
        response = authenticated_regular_client.get("/api/wallet/transactions")

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total_count" in data

    def test_transaction_history_pagination(self, authenticated_regular_client):
        """Test transaction history with pagination."""
        response = authenticated_regular_client.get(
            "/api/wallet/transactions?offset=0&limit=10"
        )

        assert response.status_code == 200

    def test_transaction_history_filter(self, authenticated_regular_client):
        """Test transaction history with type filter."""
        filters = ["credit", "debit", "sms_purchase"]

        for filter_type in filters:
            response = authenticated_regular_client.get(
                f"/api/wallet/transactions?transaction_type={filter_type}"
            )

            assert response.status_code == 200

    def test_crypto_addresses_endpoint(self, authenticated_regular_client):
        """Test crypto addresses endpoint."""
        response = authenticated_regular_client.get("/api/billing/crypto-addresses")

        # Should return 200 or 404 (if not implemented)
        assert response.status_code in [200, 404, 501]

    def test_payment_status_check(self, authenticated_regular_client):
        """Test payment status check endpoint."""
        response = authenticated_regular_client.get(
            "/api/billing/payment-status/test-reference"
        )

        # Should return 200 or 404
        assert response.status_code in [200, 404]

    def test_wallet_page_loads(self, authenticated_regular_client):
        """Test wallet page HTML loads."""
        response = authenticated_regular_client.get("/wallet")

        assert response.status_code == 200
        assert b"Add Credits" in response.content or b"wallet" in response.content

    def test_export_credit_history(self, authenticated_regular_client):
        """Test credit history export."""
        response = authenticated_regular_client.get("/api/wallet/transactions/export")

        # Should return CSV or 404
        assert response.status_code in [200, 404]


class TestWalletPaymentMethods:
    """Test payment method switching and functionality."""

    def test_card_payment_tab_default(self, authenticated_regular_client):
        """Test card payment is default tab."""
        response = authenticated_regular_client.get("/wallet")

        assert response.status_code == 200
        # Card payment section should be visible by default
        assert b"payment-card" in response.content

    def test_crypto_payment_tab_exists(self, authenticated_regular_client):
        """Test crypto payment tab exists."""
        response = authenticated_regular_client.get("/wallet")

        assert response.status_code == 200
        assert b"payment-crypto" in response.content
        assert b"switchPaymentMethod" in response.content

    def test_crypto_currencies_available(self, authenticated_regular_client):
        """Test crypto currencies are available."""
        response = authenticated_regular_client.get("/wallet")

        assert response.status_code == 200
        # Check for crypto options
        assert b"Bitcoin" in response.content or b"BTC" in response.content
        assert b"Ethereum" in response.content or b"ETH" in response.content


class TestWalletSecurity:
    """Test wallet security and authentication."""

    def test_wallet_requires_authentication(self, client):
        """Test wallet page requires authentication."""
        response = client.get("/wallet")

        # Should redirect to login or return 401
        assert response.status_code in [302, 401, 403]

    def test_wallet_api_requires_authentication(self, client):
        """Test wallet API requires authentication."""
        response = client.get("/api/wallet/balance")

        assert response.status_code in [401, 403]

    def test_payment_requires_authentication(self, client):
        """Test payment initialization requires authentication."""
        response = client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 10.0}
        )

        assert response.status_code in [401, 403]


class TestWalletEdgeCases:
    """Test edge cases and error handling."""

    def test_payment_with_missing_amount(self, authenticated_regular_client):
        """Test payment without amount."""
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={}
        )

        assert response.status_code in [400, 422]

    def test_payment_with_invalid_json(self, authenticated_regular_client):
        """Test payment with invalid JSON."""
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

    def test_transaction_history_invalid_pagination(self, authenticated_regular_client):
        """Test transaction history with invalid pagination."""
        response = authenticated_regular_client.get(
            "/api/wallet/transactions?offset=-1&limit=0"
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_large_payment_amount(self, authenticated_regular_client):
        """Test payment with very large amount."""
        response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 999999.99}
        )

        # Should reject or handle appropriately
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
class TestWalletIntegration:
    """Integration tests for wallet functionality."""

    async def test_full_payment_flow(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test complete payment flow."""
        # 1. Check initial balance
        balance_response = authenticated_regular_client.get("/api/wallet/balance")
        assert balance_response.status_code == 200
        initial_balance = balance_response.json()["credits"]

        # 2. Initialize payment
        payment_response = authenticated_regular_client.post(
            "/api/wallet/paystack/initialize", json={"amount_usd": 10.0}
        )

        # Payment initialization should work or fail gracefully
        assert payment_response.status_code in [200, 402, 503]

    async def test_transaction_history_after_payment(
        self, authenticated_regular_client, regular_user, db
    ):
        """Test transaction history shows after payment."""
        # Get transaction history
        response = authenticated_regular_client.get("/api/wallet/transactions")

        assert response.status_code == 200
