"""Tests for EmailNotificationService — all 6 notification email methods."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_notification_service import EmailNotificationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_notification(
    title="Test Title",
    message="Test message body",
    type_="system",
    link=None,
):
    n = MagicMock()
    n.title = title
    n.message = message
    n.type = type_
    n.link = link
    n.created_at = datetime.now(timezone.utc)
    return n


def _enabled_service():
    """Service instance with Resend enabled via patched settings."""
    with patch(
        "app.services.email_notification_service.get_settings"
    ) as mock_settings, patch.dict("sys.modules", {"resend": MagicMock()}):
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.smtp_host = None
        mock_settings.return_value.smtp_port = 587
        mock_settings.return_value.smtp_user = None
        mock_settings.return_value.smtp_password = None
        mock_settings.return_value.from_email = "support@vrenum.app"
        svc = EmailNotificationService()
    return svc


def _disabled_service():
    """Service instance with no credentials — disabled."""
    with patch("app.services.email_notification_service.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = None
        mock_settings.return_value.smtp_host = None
        mock_settings.return_value.smtp_port = 587
        mock_settings.return_value.smtp_user = None
        mock_settings.return_value.smtp_password = None
        mock_settings.return_value.from_email = "support@vrenum.app"
        svc = EmailNotificationService()
    return svc


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestEmailNotificationServiceInit:

    def test_enabled_with_resend_key(self):
        svc = _enabled_service()
        assert svc.enabled is True
        assert svc._mode == "resend"

    def test_disabled_without_credentials(self):
        svc = _disabled_service()
        assert svc.enabled is False
        assert svc._mode is None

    def test_enabled_with_smtp(self):
        with patch("app.services.email_notification_service.get_settings") as m:
            m.return_value.resend_api_key = None
            m.return_value.smtp_host = "smtp.gmail.com"
            m.return_value.smtp_port = 587
            m.return_value.smtp_user = "user@gmail.com"
            m.return_value.smtp_password = "pass"
            m.return_value.from_email = "user@gmail.com"
            svc = EmailNotificationService()
        assert svc.enabled is True
        assert svc._mode == "smtp"


# ---------------------------------------------------------------------------
# Disabled service — all methods return False immediately
# ---------------------------------------------------------------------------


class TestDisabledService:

    @pytest.mark.asyncio
    async def test_send_notification_email_disabled(self):
        svc = _disabled_service()
        result = await svc.send_notification_email("u@test.com", _make_notification())
        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_initiated_disabled(self):
        svc = _disabled_service()
        result = await svc.send_verification_initiated_email(
            "u@test.com", "WhatsApp", "ver-123"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_completed_disabled(self):
        svc = _disabled_service()
        result = await svc.send_verification_completed_email(
            "u@test.com", "Telegram", "ver-456", 2.50
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_low_balance_disabled(self):
        svc = _disabled_service()
        result = await svc.send_low_balance_alert_email("u@test.com", 1.50, 5.00)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_daily_digest_disabled(self):
        svc = _disabled_service()
        result = await svc.send_daily_digest_email("u@test.com", [_make_notification()])
        assert result is False

    @pytest.mark.asyncio
    async def test_send_weekly_digest_disabled(self):
        svc = _disabled_service()
        result = await svc.send_weekly_digest_email(
            "u@test.com", [_make_notification()], {"verifications": 5}
        )
        assert result is False


# ---------------------------------------------------------------------------
# Enabled service — methods reach _send_email
# ---------------------------------------------------------------------------


class TestEnabledService:

    @pytest.mark.asyncio
    async def test_send_notification_email_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_notification_email("u@test.com", _make_notification())
        assert result is True
        svc._send_email.assert_called_once()
        call_kwargs = svc._send_email.call_args
        assert call_kwargs.kwargs["to_email"] == "u@test.com"

    @pytest.mark.asyncio
    async def test_send_verification_initiated_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_verification_initiated_email(
            "u@test.com", "WhatsApp", "ver-123"
        )
        assert result is True
        svc._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_completed_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_verification_completed_email(
            "u@test.com", "Telegram", "ver-456", 2.50
        )
        assert result is True
        svc._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_low_balance_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_low_balance_alert_email("u@test.com", 1.50, 5.00)
        assert result is True
        svc._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_daily_digest_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_daily_digest_email(
            "u@test.com", [_make_notification(), _make_notification()]
        )
        assert result is True
        svc._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_weekly_digest_calls_send(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_weekly_digest_email(
            "u@test.com",
            [_make_notification()],
            {"verifications": 10, "spent": "$25.00"},
        )
        assert result is True
        svc._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_daily_digest_empty_list_returns_false(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_daily_digest_email("u@test.com", [])
        assert result is False
        svc._send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_weekly_digest_empty_list_returns_false(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        result = await svc.send_weekly_digest_email("u@test.com", [], {})
        assert result is False
        svc._send_email.assert_not_called()


# ---------------------------------------------------------------------------
# Subject line correctness
# ---------------------------------------------------------------------------


class TestSubjectLines:

    @pytest.mark.asyncio
    async def test_notification_subject_includes_type(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        notif = _make_notification(title="Payment received", type_="payment")
        await svc.send_notification_email("u@test.com", notif)
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "PAYMENT" in subject
        assert "Payment received" in subject

    @pytest.mark.asyncio
    async def test_verification_initiated_subject(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        await svc.send_verification_initiated_email("u@test.com", "Discord", "v1")
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "Discord" in subject or "verification" in subject.lower()

    @pytest.mark.asyncio
    async def test_verification_completed_subject(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        await svc.send_verification_completed_email("u@test.com", "Google", "v2", 2.50)
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "Google" in subject or "complete" in subject.lower()

    @pytest.mark.asyncio
    async def test_low_balance_subject(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        await svc.send_low_balance_alert_email("u@test.com", 1.00, 5.00)
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "balance" in subject.lower() or "low" in subject.lower()

    @pytest.mark.asyncio
    async def test_daily_digest_subject_includes_count(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        notifications = [_make_notification() for _ in range(3)]
        await svc.send_daily_digest_email("u@test.com", notifications)
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "3" in subject

    @pytest.mark.asyncio
    async def test_weekly_digest_subject(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(return_value=True)
        await svc.send_weekly_digest_email("u@test.com", [_make_notification()], {})
        subject = svc._send_email.call_args.kwargs["subject"]
        assert "weekly" in subject.lower() or "summary" in subject.lower()


# ---------------------------------------------------------------------------
# Error handling — _send_email raises, method returns False
# ---------------------------------------------------------------------------


class TestErrorHandling:

    @pytest.mark.asyncio
    async def test_notification_email_send_failure_returns_false(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(side_effect=Exception("Resend error"))
        result = await svc.send_notification_email("u@test.com", _make_notification())
        assert result is False

    @pytest.mark.asyncio
    async def test_low_balance_send_failure_returns_false(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(side_effect=Exception("Network error"))
        result = await svc.send_low_balance_alert_email("u@test.com", 1.00, 5.00)
        assert result is False

    @pytest.mark.asyncio
    async def test_digest_send_failure_returns_false(self):
        svc = _enabled_service()
        svc._send_email = AsyncMock(side_effect=Exception("Timeout"))
        result = await svc.send_daily_digest_email("u@test.com", [_make_notification()])
        assert result is False
