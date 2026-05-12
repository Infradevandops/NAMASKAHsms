"""Tests for Payment Service - Critical Business Logic

This test suite covers the most critical payment operations:
- Payment initialization
- Payment verification
- User credit operations
- Webhook signature verification
- Idempotency handling
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.transaction import PaymentLog, Transaction
from app.models.user import User
from app.services.payment_service import PaymentService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock(spec=Session)
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def payment_service(mock_db):
    """Create PaymentService instance with mocked database."""
    return PaymentService(mock_db)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = "user123"
    user.email = "test@example.com"
    user.credits = 10.0
    return user


@pytest.fixture
def mock_payment_log():
    """Create a mock payment log."""
    log = Mock(spec=PaymentLog)
    log.id = "log123"
    log.reference = "ref123"
    log.user_id = "user123"
    log.amount_usd = 50.0
    log.state = "pending"
    log.credited = False
    return log


class TestPaymentInitialization:
    """Test payment initialization logic."""

    @pytest.mark.asyncio
    async def test_initialize_payment_success(self, payment_service, mock_db):
        """Test successful payment initialization."""
        # Mock Paystack API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "reference": "ref123",
                "authorization_url": "https://paystack.com/pay/ref123",
                "access_code": "access123",
            },
        }

        with patch("requests.post", return_value=mock_response):
            result = await payment_service.initialize_payment(
                user_id="user123",
                email="test@example.com",
                amount_usd=50.0,
            )

        assert result["reference"] == "ref123"
        assert "authorization_url" in result
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_initialize_payment_with_idempotency(
        self, payment_service, mock_db, mock_payment_log
    ):
        """Test idempotency - should return cached result."""
        mock_payment_log.state = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_payment_log
        )

        result = await payment_service.initialize_payment(
            user_id="user123",
            email="test@example.com",
            amount_usd=50.0,
            idempotency_key="idempotent123",
        )

        assert result["cached"] is True
        assert result["reference"] == "ref123"

    @pytest.mark.asyncio
    async def test_initialize_payment_api_failure(self, payment_service, mock_db):
        """Test payment initialization when Paystack API fails."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid request"

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(Exception, match="Payment initialization failed"):
                await payment_service.initialize_payment(
                    user_id="user123",
                    email="test@example.com",
                    amount_usd=50.0,
                )

        assert mock_db.commit.called  # Should commit the failed state


class TestPaymentVerification:
    """Test payment verification logic."""

    @pytest.mark.asyncio
    async def test_verify_payment_success(self, payment_service):
        """Test successful payment verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": True,
            "data": {"status": "success", "amount": 5000},
        }

        with patch("requests.get", return_value=mock_response):
            result = await payment_service.verify_payment("ref123")

        assert result["status"] is True
        assert result["data"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_verify_payment_failure(self, payment_service):
        """Test payment verification when API fails."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Transaction not found"

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(Exception, match="Payment verification failed"):
                await payment_service.verify_payment("invalid_ref")


class TestUserCredit:
    """Test user credit operations - CRITICAL for financial integrity."""

    def test_credit_user_success(
        self, payment_service, mock_db, mock_user, mock_payment_log
    ):
        """Test successful user credit operation."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
            mock_payment_log,
            mock_user,
        ]

        result = payment_service.credit_user(
            user_id="user123", amount=50.0, reference="ref123"
        )

        assert result is True
        assert mock_user.credits == 60.0  # 10.0 + 50.0
        assert mock_payment_log.credited is True
        assert mock_payment_log.state == "completed"
        assert mock_db.commit.called

    def test_credit_user_already_credited(
        self, payment_service, mock_db, mock_payment_log
    ):
        """Test idempotency - should not double-credit."""
        mock_payment_log.credited = True
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
            mock_payment_log
        )

        result = payment_service.credit_user(
            user_id="user123", amount=50.0, reference="ref123"
        )

        assert result is True
        # Should not add to database again
        assert not mock_db.add.called

    def test_credit_user_payment_not_found(self, payment_service, mock_db):
        """Test credit when payment log doesn't exist."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
            None
        )

        with pytest.raises(ValueError, match="Payment log .* not found"):
            payment_service.credit_user(
                user_id="user123", amount=50.0, reference="invalid_ref"
            )

    def test_credit_user_user_not_found(
        self, payment_service, mock_db, mock_payment_log
    ):
        """Test credit when user doesn't exist."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
            mock_payment_log,
            None,
        ]

        with pytest.raises(ValueError, match="User .* not found"):
            payment_service.credit_user(
                user_id="invalid_user", amount=50.0, reference="ref123"
            )

    def test_credit_user_database_error(
        self, payment_service, mock_db, mock_user, mock_payment_log
    ):
        """Test credit operation when database fails."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
            mock_payment_log,
            mock_user,
        ]
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            payment_service.credit_user(
                user_id="user123", amount=50.0, reference="ref123"
            )

        assert mock_db.rollback.called


class TestWebhookSignature:
    """Test webhook signature verification - CRITICAL for security."""

    def test_verify_webhook_signature_valid(self, payment_service):
        """Test valid webhook signature."""
        payload = b'{"event": "charge.success"}'
        # This is a mock signature - in real tests, generate actual HMAC
        signature = "valid_signature_hash"

        with patch("hmac.compare_digest", return_value=True):
            result = payment_service.verify_webhook_signature(payload, signature)

        assert result is True

    def test_verify_webhook_signature_invalid(self, payment_service):
        """Test invalid webhook signature."""
        payload = b'{"event": "charge.success"}'
        signature = "invalid_signature"

        with patch("hmac.compare_digest", return_value=False):
            result = payment_service.verify_webhook_signature(payload, signature)

        assert result is False

    def test_verify_webhook_signature_exception(self, payment_service):
        """Test webhook signature verification with exception."""
        payload = b'{"event": "charge.success"}'
        signature = "signature"

        with patch("hmac.new", side_effect=Exception("HMAC error")):
            result = payment_service.verify_webhook_signature(payload, signature)

        assert result is False


class TestWebhookProcessing:
    """Test webhook processing with retry logic."""

    @pytest.mark.asyncio
    async def test_process_webhook_with_retry_success(
        self, payment_service, mock_db, mock_user, mock_payment_log
    ):
        """Test successful webhook processing on first attempt."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
            mock_payment_log,
            mock_user,
        ]

        with patch("app.core.cache.get_redis") as mock_redis:
            mock_lock = Mock()
            mock_lock.acquire.return_value = True
            mock_redis.return_value.lock.return_value = mock_lock

            result = await payment_service.process_webhook_with_retry(
                user_id="user123", amount=50.0, reference="ref123"
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_process_webhook_with_retry_failure(
        self, payment_service, mock_db, mock_payment_log
    ):
        """Test webhook processing fails after max retries."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
            None
        )

        with patch("app.core.cache.get_redis") as mock_redis:
            mock_lock = Mock()
            mock_lock.acquire.return_value = True
            mock_redis.return_value.lock.return_value = mock_lock

            with pytest.raises(ValueError):
                await payment_service.process_webhook_with_retry(
                    user_id="user123",
                    amount=50.0,
                    reference="invalid_ref",
                    max_retries=2,
                )


class TestPaymentHistory:
    """Test payment history retrieval."""

    def test_get_payment_history(self, payment_service, mock_db):
        """Test retrieving payment history."""
        mock_logs = [
            Mock(
                reference="ref1",
                amount_usd=50.0,
                status="success",
                created_at=datetime.now(timezone.utc),
            ),
            Mock(
                reference="ref2",
                amount_usd=100.0,
                status="pending",
                created_at=datetime.now(timezone.utc),
            ),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_logs
        )

        result = payment_service.get_payment_history("user123", limit=10)

        assert len(result) == 2
        assert result[0]["reference"] == "ref1"
        assert result[1]["amount_usd"] == 100.0

    def test_get_payment_summary(self, payment_service, mock_db):
        """Test retrieving payment summary."""
        mock_logs = [
            Mock(amount_usd=50.0, status="success"),
            Mock(amount_usd=100.0, status="success"),
            Mock(amount_usd=25.0, status="failed"),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_logs

        result = payment_service.get_payment_summary("user123")

        assert result["total_paid"] == 150.0  # Only successful payments
        assert result["transaction_count"] == 3
        assert result["successful"] == 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_initialize_payment_zero_amount(self, payment_service):
        """Test payment initialization with zero amount."""
        # Should be handled by validation layer, but test service behavior
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid amount"

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(Exception):
                await payment_service.initialize_payment(
                    user_id="user123",
                    email="test@example.com",
                    amount_usd=0.0,
                )

    @pytest.mark.asyncio
    async def test_initialize_payment_negative_amount(self, payment_service):
        """Test payment initialization with negative amount."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid amount"

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(Exception):
                await payment_service.initialize_payment(
                    user_id="user123",
                    email="test@example.com",
                    amount_usd=-50.0,
                )

    def test_credit_user_concurrent_requests(
        self, payment_service, mock_db, mock_payment_log, mock_user
    ):
        """Test concurrent credit requests (race condition)."""
        from sqlalchemy.exc import IntegrityError

        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
            mock_payment_log,
            mock_user,
        ]
        mock_db.commit.side_effect = IntegrityError("", "", "")

        # Should handle gracefully and return True (idempotent)
        result = payment_service.credit_user(
            user_id="user123", amount=50.0, reference="ref123"
        )

        assert result is True
        assert mock_db.rollback.called


# Integration test markers
pytestmark = pytest.mark.unit
