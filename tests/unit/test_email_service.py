

from unittest.mock import patch
import pytest
from app.services.email_service import EmailService

class TestEmailService:
    @pytest.fixture
    def service(self):

        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_host = "localhost"
            mock_settings.return_value.smtp_port = 587
            mock_settings.return_value.smtp_user = "user"
            mock_settings.return_value.smtp_password = "pass"
            mock_settings.return_value.from_email = "test@namaskah.com"
        return EmailService()

        @pytest.mark.asyncio
        @patch("app.services.email_service.EmailService._send_email")
    async def test_send_payment_receipt(self, mock_send, service):
        details = {
            "reference": "REF123",
            "amount_usd": 10.0,
            "credits_added": 10.0,
            "new_balance": 20.0,
        }
        res = await service.send_payment_receipt("user@example.com", details)
        assert res is True
        assert mock_send.called

        @pytest.mark.asyncio
        @patch("app.services.email_service.EmailService._send_email")
    async def test_send_payment_failed_alert(self, mock_send, service):
        details = {"reference": "REF123", "amount_usd": 10.0, "reason": "Declined"}
        res = await service.send_payment_failed_alert("user@example.com", details)
        assert res is True
        assert mock_send.called

        @pytest.mark.asyncio
        @patch("app.services.email_service.EmailService._send_email")
    async def test_send_refund_notification(self, mock_send, service):
        details = {"reference": "REF123", "amount": 5.0, "new_balance": 15.0}
        res = await service.send_refund_notification("user@example.com", details)
        assert res is True
        assert mock_send.called

    def test_disabled_service(self):

        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_host = None
            service = EmailService()
            assert service.enabled is False

        @pytest.mark.asyncio
        @patch("smtplib.SMTP")
    async def test_actual_smtp_send(self, mock_smtp, service):
        mock_server = mock_smtp.return_value.__enter__.return_value
        await service._send_email("to@ex.com", "Sub", "<html>Body</html>")
        assert mock_server.login.called
        assert mock_server.sendmail.called