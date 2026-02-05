"""Unit tests for SMS Polling Service."""


# Sample message response from TextVerified

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.user import User
from app.models.verification import Verification
from app.services.sms_polling_service import SMSPollingService

SAMPLE_SMS_RESPONSE = {
    "id": "msg_123",
    "messages": [
        {
            "id": "m1",
            "text": "Your verification code is 123456",
            "received_at": "2024-01-01T00:00:00Z",
        }
    ],
    "status": "COMPLETED",
}

SAMPLE_TIMEOUT_RESPONSE = {"id": "msg_123", "messages": [], "status": "TIMEOUT"}

SAMPLE_PENDING_RESPONSE = {"id": "msg_123", "messages": [], "status": "PENDING"}


@pytest.fixture
def polling_service():

    service = SMSPollingService()
    service.textverified = AsyncMock()
    return service


@pytest.fixture
def mock_settings():

with patch("app.services.sms_polling_service.settings") as mock_settings:
        mock_settings.sms_polling_initial_interval_seconds = 0.01
        mock_settings.sms_polling_max_minutes = 10
        mock_settings.sms_polling_error_backoff_seconds = 0.01
        mock_settings.sms_polling_later_interval_seconds = 0.01
        yield mock_settings


@pytest.fixture
def mock_verification(db_session):

    """Create a pending verification."""
    # Ensure user exists first
    user = User(email="poll_test@example.com", credits=10.0)
    db_session.add(user)
    db_session.commit()

    ver = Verification(
        id="ver_123",
        user_id=user.id,
        status="pending",
        provider="textverified",
        phone_number="1234567890",
        country="US",
        service_name="whatsapp",
        cost=1.0,
        activation_id="tv_123",  # Important for polling
    )
    db_session.add(ver)
    db_session.commit()
    return ver


@pytest.mark.asyncio
async def test_poll_verification_success(db_session, polling_service, mock_settings, mock_verification):
    """Test polling successfully receiving an SMS."""
    # Mock TextVerified response sequence: Pending -> Success
    polling_service.textverified.check_sms.side_effect = [
        SAMPLE_PENDING_RESPONSE,
        SAMPLE_SMS_RESPONSE,
    ]

    # Mock SessionLocal to return our test session but prevent it from being closed
    # which would break subsequent assertions
    session_mock = MagicMock(wraps=db_session)
    session_mock.close = MagicMock()
    session_mock.commit = MagicMock(side_effect=db_session.commit)
    session_mock.query = db_session.query
    session_mock.add = db_session.add

with patch("app.services.sms_polling_service.SessionLocal", return_value=session_mock):
        # We also need to mock NotificationService to avoid errors or just let it fail silently (it has try/except)
        # But to be clean, let's mock it.
with patch("app.services.sms_polling_service.NotificationService") as MockNotify:

            # RUN
            await polling_service._poll_verification(mock_verification.id, "1234567890")

            # ASSERT
            db_session.refresh(mock_verification)
            assert mock_verification.status == "completed"
            assert mock_verification.sms_code == "123456"
            assert "Your verification code is 123456" in mock_verification.sms_text


@pytest.mark.asyncio
async def test_poll_verification_timeout(db_session, polling_service, mock_settings, mock_verification):
    """Test polling handling a timeout response."""
    polling_service.textverified.check_sms.return_value = SAMPLE_TIMEOUT_RESPONSE

    session_mock = MagicMock(wraps=db_session)
    session_mock.close = MagicMock()
    session_mock.commit = MagicMock(side_effect=db_session.commit)
    session_mock.query = db_session.query

with patch("app.services.sms_polling_service.SessionLocal", return_value=session_mock):
        await polling_service._poll_verification(mock_verification.id, "1234567890")

        db_session.refresh(mock_verification)
        assert mock_verification.status == "timeout"


@pytest.mark.asyncio
async def test_poll_stops_if_status_changes(db_session, polling_service, mock_settings, mock_verification):
    """Test polling stops if verification status changes externally (e.g. cancelled)."""
    # Change status to cancelled
    mock_verification.status = "cancelled"
    db_session.commit()

    session_mock = MagicMock(wraps=db_session)
    session_mock.close = MagicMock()
    session_mock.query = db_session.query

with patch("app.services.sms_polling_service.SessionLocal", return_value=session_mock):
        await polling_service._poll_verification(mock_verification.id, "1234567890")

    # Should have stopped immediately without calling check_sms
    polling_service.textverified.check_sms.assert_not_called()


@pytest.mark.asyncio
async def test_start_polling_creates_task(polling_service):
    """Test start_polling adds a task to dictionary."""
    # We mock _poll_verification to avoid running the loop
with patch.object(polling_service, "_poll_verification", new_callable=AsyncMock) as mock_poll:
        await polling_service.start_polling("v1", "123")

        assert "v1" in polling_service.polling_tasks
        assert not polling_service.polling_tasks["v1"].done()

        # Cleanup
        await polling_service.stop_polling("v1")


@pytest.mark.asyncio
async def test_stop_polling_cancels_task(polling_service):
    """Test stop_polling removes and cancels task."""

    # Create a dummy task
async def dummy_task():
        await asyncio.sleep(1)

    task = asyncio.create_task(dummy_task())
    polling_service.polling_tasks["v1"] = task

    await polling_service.stop_polling("v1")

    # Give the loop a chance to process the cancellation
try:
        await task
except asyncio.CancelledError:
        pass

    assert "v1" not in polling_service.polling_tasks
    assert task.cancelled()


@pytest.mark.asyncio
async def test_background_service_flow(db_session, polling_service, mock_settings, mock_verification):
    """Test background service picks up pending verifications."""

    # Mock start_polling to verify it gets called
with patch.object(polling_service, "start_polling", new_callable=AsyncMock) as mock_start:

        # Run service for a brief moment
        polling_service.is_running = True

        # We need to run start_background_service but kill it after one iteration
        # Easy way: mock sleep to raise an exception or change is_running
async def stop_after_one_loop(*args):
            polling_service.is_running = False

with patch("asyncio.sleep", side_effect=stop_after_one_loop):
            session_mock = MagicMock(wraps=db_session)
            session_mock.close = MagicMock()
            session_mock.query = db_session.query

with patch(
                "app.services.sms_polling_service.SessionLocal",
                return_value=session_mock,
            ):
try:
                    await polling_service.start_background_service()
except Exception:
                    pass  # End of loop

        # Verify it found the pending verification and tried to start polling
        mock_start.assert_called_with(mock_verification.id, mock_verification.phone_number)
