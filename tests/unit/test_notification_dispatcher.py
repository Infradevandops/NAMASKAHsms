"""Tests for NotificationDispatcher."""

from unittest.mock import MagicMock
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


@pytest.mark.asyncio
async def test_notify_verification_started(dispatcher):
    """Test verification started notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value={"id": 1, "title": "Test"})
    
    # Use patch to mock _broadcast_notification to avoid WebSocket complications
    with patch.object(dispatcher, "_broadcast_notification"):
        result = await dispatcher.notify_verification_started(
            user_id="user123",
            verification_id="v123",
            service="Gmail",
            phone_number="+14155550101",
            cost=2.50
        )

        assert result is True
        dispatcher.notification_service.create_notification.assert_called_once()
        call_args = dispatcher.notification_service.create_notification.call_args
        assert call_args[1]["user_id"] == "user123"
        assert call_args[1]["notification_type"] == "verification_started"
        assert "Gmail" in call_args[1]["message"]

@pytest.mark.asyncio
async def test_notify_verification_completed(dispatcher):
    """Test verification completed notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value={"id": 1, "title": "Test"})
    
    with patch.object(dispatcher, "_broadcast_notification"):
        result = await dispatcher.notify_verification_completed(
            user_id="user123",
            verification_id="v123",
            service="Twitter",
            phone_number="+14155550101"
        )

        assert result is True
        dispatcher.notification_service.create_notification.assert_called_once()
        call_args = dispatcher.notification_service.create_notification.call_args
        assert call_args[1]["notification_type"] == "verification_completed"

@pytest.mark.asyncio
async def test_notify_verification_failed(dispatcher):
    """Test verification failed notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value={"id": 1, "title": "Test"})
    
    with patch.object(dispatcher, "_broadcast_notification"):
        result = await dispatcher.notify_verification_failed(
            user_id="user123",
            verification_id="v123",
            service="Facebook",
            reason="Timeout"
        )

        assert result is True
        dispatcher.notification_service.create_notification.assert_called_once()
        call_args = dispatcher.notification_service.create_notification.call_args
        assert call_args[1]["notification_type"] == "verification_failed"
        assert "Timeout" in call_args[1]["message"]

@pytest.mark.asyncio
async def test_notify_payment_completed(dispatcher):
    """Test payment completed notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value={"id": 1, "title": "Test"})
    
    with patch.object(dispatcher, "_broadcast_notification"):
        result = await dispatcher.notify_payment_completed("user123", 50.00, 100.00)

        assert result is True
        dispatcher.notification_service.create_notification.assert_called_once()
        call_args = dispatcher.notification_service.create_notification.call_args
        assert call_args[1]["notification_type"] == "payment_completed"
        assert "50.00" in call_args[1]["message"]

@pytest.mark.asyncio
async def test_notify_verification_timeout(dispatcher):
    """Test verification timeout notification."""
    dispatcher.notification_service.create_notification = MagicMock(return_value={"id": 1, "title": "Test"})
    
    with patch.object(dispatcher, "_broadcast_notification"):
        result = await dispatcher.notify_verification_timeout("user123", "v123", "Telegram", 1.50)

        assert result is True
        dispatcher.notification_service.create_notification.assert_called_once()
        call_args = dispatcher.notification_service.create_notification.call_args
        assert call_args[1]["notification_type"] == "verification_timeout"
        assert "1.50" in call_args[1]["message"]



def test_on_verification_created_exception(dispatcher):
    """Test verification created with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_verification_created(mock_verification)

    assert result is False


def test_on_sms_received_exception(dispatcher):
    """Test SMS received with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_sms_received(mock_verification)

    assert result is False


def test_on_verification_failed_exception(dispatcher):
    """Test verification failed with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_verification_failed(mock_verification, "Error")

    assert result is False


def test_on_credit_deducted_exception(dispatcher):
    """Test credit deducted with exception."""
    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_credit_deducted("user123", 5.0, "Service")

    assert result is False


def test_on_refund_issued_exception(dispatcher):
    """Test refund issued with exception."""
    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_refund_issued("user123", 10.0, "Reason")

    assert result is False


def test_on_balance_low_exception(dispatcher):
    """Test balance low with exception."""
    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_balance_low("user123", 2.5)

    assert result is False


def test_on_verification_completed_exception(dispatcher):
    """Test verification completed with exception."""
    mock_verification = MagicMock()
    mock_verification.user_id = "user123"

    dispatcher.notification_service.create_notification = MagicMock(
        side_effect=Exception("DB Error")
    )

    result = dispatcher.on_verification_completed(mock_verification)

    assert result is False
