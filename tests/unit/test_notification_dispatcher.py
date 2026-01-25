"""Tests for NotificationDispatcher."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.notification_dispatcher import NotificationDispatcher


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def dispatcher(mock_db):
    return NotificationDispatcher(mock_db)


def test_dispatcher_init(mock_db):
    """Test NotificationDispatcher initialization."""
    dispatcher = NotificationDispatcher(mock_db)
    assert dispatcher.db == mock_db
    assert dispatcher.notification_service is not None


def test_on_verification_created(dispatcher):
    """Test verification created notification."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"
    mock_verification.service_name = "Gmail"
    mock_verification.id = "v123"

    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_verification_created(mock_verification)

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["user_id"] == "user123"
    assert call_args[1]["notification_type"] == "verification_initiated"
    assert "Gmail" in call_args[1]["message"]


def test_on_sms_received(dispatcher):
    """Test SMS received notification."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"
    mock_verification.service_name = "Twitter"
    mock_verification.sms_code = "123456"
    mock_verification.id = "v123"

    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_sms_received(mock_verification)

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "sms_received"
    assert "123456" in call_args[1]["message"]


def test_on_verification_failed(dispatcher):
    """Test verification failed notification."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"
    mock_verification.service_name = "Facebook"
    mock_verification.id = "v123"

    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_verification_failed(mock_verification, "Timeout")

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "verification_failed"
    assert "Timeout" in call_args[1]["message"]


def test_on_credit_deducted(dispatcher):
    """Test credit deducted notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_credit_deducted("user123", 5.50, "SMS Verification")

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "credit_deducted"
    assert "5.50" in call_args[1]["message"]


def test_on_refund_issued(dispatcher):
    """Test refund issued notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_refund_issued("user123", 10.00, "Failed verification")

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "refund_issued"
    assert "10.00" in call_args[1]["message"]


def test_on_balance_low(dispatcher):
    """Test balance low notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_balance_low("user123", 2.50)

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "balance_low"
    assert "2.50" in call_args[1]["message"]


def test_on_verification_completed(dispatcher):
    """Test verification completed notification."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"
    mock_verification.service_name = "LinkedIn"
    mock_verification.id = "v123"

    dispatcher.notification_service.create_notification = MagicMock(return_value=True)

    result = dispatcher.on_verification_completed(mock_verification)

    assert result is True
    dispatcher.notification_service.create_notification.assert_called_once()
    call_args = dispatcher.notification_service.create_notification.call_args
    assert call_args[1]["notification_type"] == "verification_complete"
    assert "LinkedIn" in call_args[1]["message"]


def test_on_verification_created_exception(dispatcher):
    """Test verification created with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_verification_created(mock_verification)

    assert result is False


def test_on_sms_received_exception(dispatcher):
    """Test SMS received with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_sms_received(mock_verification)

    assert result is False


def test_on_verification_failed_exception(dispatcher):
    """Test verification failed with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_verification_failed(mock_verification, "Error")

    assert result is False


def test_on_credit_deducted_exception(dispatcher):
    """Test credit deducted with exception."""
    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_credit_deducted("user123", 5.0, "Service")

    assert result is False


def test_on_refund_issued_exception(dispatcher):
    """Test refund issued with exception."""
    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_refund_issued("user123", 10.0, "Reason")

    assert result is False


def test_on_balance_low_exception(dispatcher):
    """Test balance low with exception."""
    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_balance_low("user123", 2.5)

    assert result is False


def test_on_verification_completed_exception(dispatcher):
    """Test verification completed with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(side_effect=Exception("DB Error"))

    result = dispatcher.on_verification_completed(mock_verification)

    assert result is False
