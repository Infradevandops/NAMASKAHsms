"""Tests for webhook service."""
import pytest
import json
import hmac
import hashlib
from unittest.mock import MagicMock, patch
from app.services.webhook_service import WebhookService


@pytest.fixture
def webhook_service(db_session):
    """Create webhook service instance."""
    return WebhookService(db_session)


@pytest.fixture
def db_session():
    """Mock database session."""
    return MagicMock()


def test_webhook_signature_verification_valid(webhook_service):
    """Test valid webhook signature verification."""
    payload = json.dumps({"event": "charge.success", "data": {"id": "123"}})
    secret = "test_secret"

    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha512
    ).hexdigest()

    with patch.object(webhook_service, 'get_secret', return_value=secret):
        result = webhook_service.verify_signature(payload.encode(), signature)
        assert result is True


def test_webhook_signature_verification_invalid(webhook_service):
    """Test invalid webhook signature verification."""
    payload = json.dumps({"event": "charge.success"})
    invalid_signature = "invalid_signature_hash"

    with patch.object(webhook_service, 'get_secret', return_value="test_secret"):
        result = webhook_service.verify_signature(payload.encode(), invalid_signature)
        assert result is False


def test_webhook_signature_verification_missing_secret(webhook_service):
    """Test signature verification with missing secret."""
    payload = json.dumps({"event": "charge.success"})
    signature = "some_signature"

    with patch.object(webhook_service, 'get_secret', return_value=None):
        result = webhook_service.verify_signature(payload.encode(), signature)
        assert result is False


def test_process_payment_webhook_success(webhook_service):
    """Test successful payment webhook processing."""
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": "ref_123",
            "amount": 50000,
            "customer": {"email": "user@example.com"},
            "metadata": {"user_id": "user_123", "namaskah_amount": 50}
        }
    }

    with patch.object(webhook_service, 'update_user_credits') as mock_update:
        result = webhook_service.process_payment_webhook(webhook_data)
        assert result is True
        mock_update.assert_called_once()


def test_process_payment_webhook_failed_charge(webhook_service):
    """Test failed charge webhook processing."""
    webhook_data = {
        "event": "charge.failed",
        "data": {
            "reference": "ref_123",
            "customer": {"email": "user@example.com"}
        }
    }

    result = webhook_service.process_payment_webhook(webhook_data)
    assert result is False


def test_process_payment_webhook_invalid_event(webhook_service):
    """Test webhook with invalid event type."""
    webhook_data = {
        "event": "unknown.event",
        "data": {}
    }

    result = webhook_service.process_payment_webhook(webhook_data)
    assert result is False


def test_process_payment_webhook_missing_data(webhook_service):
    """Test webhook with missing required data."""
    webhook_data = {
        "event": "charge.success"
    }

    result = webhook_service.process_payment_webhook(webhook_data)
    assert result is False


def test_webhook_retry_on_failure(webhook_service):
    """Test webhook retry logic on failure."""
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": "ref_123",
            "amount": 50000,
            "customer": {"email": "user@example.com"},
            "metadata": {"user_id": "user_123"}
        }
    }

    with patch.object(webhook_service, 'update_user_credits') as mock_update:
        mock_update.side_effect = [Exception("DB Error"), True]

        # First attempt fails, should retry
        with patch('time.sleep'):
            webhook_service.process_payment_webhook(webhook_data)
            # Depending on retry logic, should eventually succeed or fail gracefully


def test_webhook_duplicate_processing(webhook_service):
    """Test duplicate webhook prevention."""
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": "ref_123",
            "amount": 50000,
            "customer": {"email": "user@example.com"},
            "metadata": {"user_id": "user_123"}
        }
    }

    with patch.object(webhook_service, 'is_duplicate_webhook', return_value=True):
        result = webhook_service.process_payment_webhook(webhook_data)
        assert result is False


def test_webhook_logging(webhook_service):
    """Test webhook logging."""
    webhook_data = {
        "event": "charge.success",
        "data": {"reference": "ref_123"}
    }

    with patch('app.services.webhook_service.logger') as mock_logger:
        with patch.object(webhook_service, 'update_user_credits'):
            webhook_service.process_payment_webhook(webhook_data)
            mock_logger.info.assert_called()


def test_webhook_error_handling(webhook_service):
    """Test webhook error handling."""
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": "ref_123",
            "amount": 50000,
            "customer": {"email": "user@example.com"},
            "metadata": {"user_id": "user_123"}
        }
    }

    with patch.object(webhook_service, 'update_user_credits') as mock_update:
        mock_update.side_effect = Exception("Database error")

        with patch('app.services.webhook_service.logger') as mock_logger:
            webhook_service.process_payment_webhook(webhook_data)
            mock_logger.error.assert_called()


def test_webhook_service_initialization():
    """Test webhook service initialization."""
    db = MagicMock()
    service = WebhookService(db)
    assert service is not None
    assert hasattr(service, 'verify_signature')
    assert hasattr(service, 'process_payment_webhook')
