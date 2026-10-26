from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_service import EmailService


class TestEmailService:
    @pytest.fixture
    def smtp_mock(self):
        """Mock SMTP server."""
        mock_server = MagicMock()
        mock_server.login = MagicMock()
        mock_server.sendmail = MagicMock()
        mock_server.starttls = MagicMock()
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=None)
        return mock_server

    @pytest.fixture
    def service(self, smtp_mock):
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_host = "localhost"
            mock_settings.return_value.smtp_port = 587
            mock_settings.return_value.smtp_username = "user"
            mock_settings.return_value.smtp_password = "pass"
            mock_settings.return_value.resend_api_key = None
            mock_settings.return_value.from_email = "test@vrenum.app"
            with patch("smtplib.SMTP", return_value=smtp_mock):
                return EmailService()

    @pytest.mark.asyncio
    async def test_send_payment_receipt(self, service, smtp_mock):
        with patch("smtplib.SMTP", return_value=smtp_mock):
            details = {
                "reference": "REF123",
                "amount_usd": 10.0,
                "credits_added": 10.0,
                "new_balance": 20.0,
            }
            res = await service.send_payment_receipt("user@example.com", details)
            assert res is True
            assert smtp_mock.login.called
            assert smtp_mock.sendmail.called

    @pytest.mark.asyncio
    async def test_send_payment_failed_alert(self, service, smtp_mock):
        with patch("smtplib.SMTP", return_value=smtp_mock):
            details = {"reference": "REF123", "amount_usd": 10.0, "reason": "Declined"}
            res = await service.send_payment_failed_alert("user@example.com", details)
            assert res is True
            assert smtp_mock.login.called
            assert smtp_mock.sendmail.called

    @pytest.mark.asyncio
    async def test_send_refund_notification(self, service, smtp_mock):
        with patch("smtplib.SMTP", return_value=smtp_mock):
            details = {"reference": "REF123", "amount": 5.0, "new_balance": 15.0}
            res = await service.send_refund_notification("user@example.com", details)
            assert res is True
            assert smtp_mock.login.called
            assert smtp_mock.sendmail.called

    def test_disabled_service(self):
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_host = None
            mock_settings.return_value.resend_api_key = None
            service = EmailService()
            assert service.enabled is False

    @pytest.mark.asyncio
    async def test_actual_smtp_send(self, service, smtp_mock):
        with patch("smtplib.SMTP", return_value=smtp_mock):
            await service._send("to@ex.com", "Sub", "<html>Body</html>")
            assert smtp_mock.login.called
            assert smtp_mock.sendmail.called
