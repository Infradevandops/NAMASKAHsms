"""Tests for crypto payment endpoints."""

from unittest.mock import patch

import pytest

from app.models.transaction import PaymentLog, Transaction
from app.models.user import User


@pytest.fixture
def auth(regular_user_token):
    return {"Authorization": f"Bearer {regular_user_token}"}


class TestCryptoAddresses:
    """Test GET /wallet/crypto/addresses."""

    def test_returns_configured_addresses(self, client, auth):
        """Returns addresses when env vars are set."""
        with patch("app.api.billing.wallet_endpoints.settings") as mock_settings:
            mock_settings.btc_address = "bc1qtest123"
            mock_settings.eth_address = "0xtest456"
            mock_settings.sol_address = "soltest789"
            mock_settings.ltc_address = None  # LTC not configured

            response = client.get("/api/wallet/crypto/addresses", headers=auth)

        assert response.status_code == 200
        data = response.json()
        assert data["btc_address"] == "bc1qtest123"
        assert data["eth_address"] == "0xtest456"
        assert data["sol_address"] == "soltest789"
        assert "ltc_address" not in data  # None values excluded

    def test_503_when_no_addresses_configured(self, client, auth):
        """Returns 503 when no addresses are configured."""
        with patch("app.api.billing.wallet_endpoints.settings") as mock_settings:
            mock_settings.btc_address = None
            mock_settings.eth_address = None
            mock_settings.sol_address = None
            mock_settings.ltc_address = None

            response = client.get("/api/wallet/crypto/addresses", headers=auth)

        assert response.status_code == 503

    def test_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/wallet/crypto/addresses")
        assert response.status_code in [401, 403]


class TestCryptoIntent:
    """Test POST /wallet/crypto/intent."""

    def test_records_intent_successfully(self, client, auth, db_session, regular_user):
        """Records intent and creates pending transaction."""
        response = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 20.0,
                "currency": "btc",
                "crypto_amount": 0.00030,
                "address": "bc1qtest123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "intent_id" in data
        assert data["intent_id"].startswith("crypto_btc_")

        # Verify PaymentLog created
        log = (
            db_session.query(PaymentLog)
            .filter(PaymentLog.reference == data["intent_id"])
            .first()
        )
        assert log is not None
        assert log.amount_usd == 20.0
        assert log.state == "pending"
        assert log.payment_method == "crypto_btc"

        # Verify Transaction created
        tx = (
            db_session.query(Transaction)
            .filter(Transaction.reference == data["intent_id"])
            .first()
        )
        assert tx is not None
        assert tx.type == "credit_pending"
        assert tx.status == "pending"

    def test_rejects_invalid_currency(self, client, auth):
        """Rejects unsupported currency."""
        response = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 10.0,
                "currency": "doge",  # not in allowed list
                "crypto_amount": 100.0,
                "address": "Dtest",
            },
        )
        assert response.status_code == 422

    def test_rejects_zero_amount(self, client, auth):
        """Rejects zero or negative amounts."""
        response = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 0,
                "currency": "btc",
                "crypto_amount": 0,
                "address": "bc1qtest",
            },
        )
        assert response.status_code == 422

    def test_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.post("/api/wallet/crypto/intent", json={})
        assert response.status_code in [401, 403]


class TestCryptoConfirm:
    """Test POST /wallet/crypto/confirm."""

    def test_confirms_pending_intent(self, client, auth, db_session, regular_user):
        """Moves pending intent to processing state."""
        # First create an intent
        intent_res = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 15.0,
                "currency": "eth",
                "crypto_amount": 0.005,
                "address": "0xtest",
            },
        )
        intent_id = intent_res.json()["intent_id"]

        # Now confirm it
        response = client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={
                "intent_id": intent_id,
                "transaction_hash": "0xabc123def456",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify state changed to processing
        log = (
            db_session.query(PaymentLog)
            .filter(PaymentLog.reference == intent_id)
            .first()
        )
        assert log.state == "processing"
        assert "0xabc123def456" in log.error_message

    def test_confirm_without_hash(self, client, auth, db_session, regular_user):
        """Confirm works without transaction hash."""
        intent_res = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 10.0,
                "currency": "sol",
                "crypto_amount": 0.15,
                "address": "soltest",
            },
        )
        intent_id = intent_res.json()["intent_id"]

        response = client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={"intent_id": intent_id},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_cannot_confirm_nonexistent_intent(self, client, auth):
        """Returns 404 for unknown intent."""
        response = client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={"intent_id": "crypto_btc_nonexistent"},
        )
        assert response.status_code == 404

    def test_cannot_double_confirm(self, client, auth, db_session, regular_user):
        """Cannot confirm an already-processing intent."""
        intent_res = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 10.0,
                "currency": "btc",
                "crypto_amount": 0.00015,
                "address": "bc1qtest",
            },
        )
        intent_id = intent_res.json()["intent_id"]

        # First confirm
        client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={"intent_id": intent_id},
        )

        # Second confirm should return error
        response = client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={"intent_id": intent_id},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.post("/api/wallet/crypto/confirm", json={"intent_id": "x"})
        assert response.status_code in [401, 403]


class TestCryptoFullFlow:
    """End-to-end crypto payment flow."""

    def test_full_flow_btc(self, client, auth, db_session, regular_user):
        """Full BTC flow: addresses → intent → confirm."""
        with patch("app.api.billing.wallet_endpoints.settings") as mock_settings:
            mock_settings.btc_address = "bc1qprod123"
            mock_settings.eth_address = "0xprod456"
            mock_settings.sol_address = "solprod789"
            mock_settings.ltc_address = None

            # Step 1: Get addresses
            addr_res = client.get("/api/wallet/crypto/addresses", headers=auth)
            assert addr_res.status_code == 200
            assert addr_res.json()["btc_address"] == "bc1qprod123"

        # Step 2: Record intent
        intent_res = client.post(
            "/api/wallet/crypto/intent",
            headers=auth,
            json={
                "amount_usd": 50.0,
                "currency": "btc",
                "crypto_amount": 0.00075,
                "address": "bc1qprod123",
            },
        )
        assert intent_res.status_code == 200
        intent_id = intent_res.json()["intent_id"]

        # Step 3: Confirm sent
        confirm_res = client.post(
            "/api/wallet/crypto/confirm",
            headers=auth,
            json={
                "intent_id": intent_id,
                "transaction_hash": "btctxhash123",
            },
        )
        assert confirm_res.status_code == 200

        # Verify audit trail — pending_deposits should include this
        stats_res = client.get("/api/wallet/stats", headers=auth)
        assert stats_res.status_code == 200
        assert stats_res.json()["pending_deposits"] >= 1
