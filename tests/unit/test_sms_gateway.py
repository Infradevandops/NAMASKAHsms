"""Unit tests for SMSGateway service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.sms_gateway import SMSGateway


@pytest.fixture
def sms_gateway():
    return SMSGateway()


@pytest.fixture
def twilio_gateway():
    return SMSGateway(provider="twilio")


@pytest.fixture
def webhook_gateway():
    return SMSGateway(provider="webhook")


@pytest.fixture
def manual_gateway():
    return SMSGateway(provider="manual")


class TestInitialization:
    def test_defaults_to_twilio_provider(self):
        gateway = SMSGateway()
        assert gateway.provider == "twilio"

    def test_accepts_custom_provider(self):
        gateway = SMSGateway(provider="webhook")
        assert gateway.provider == "webhook"


class TestSendSMS:
    @pytest.mark.asyncio
    async def test_sends_via_twilio(self, twilio_gateway):
        result = await twilio_gateway.send_sms("+1234567890", "Test message")
        assert result["status"] == "sent"
        assert result["provider"] == "twilio"

    @pytest.mark.asyncio
    async def test_sends_via_webhook(self, webhook_gateway):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_gateway.send_sms("+1234567890", "Test message")
            assert result["status"] == "sent"
            assert result["provider"] == "webhook"

    @pytest.mark.asyncio
    async def test_manual_provider_returns_manual_status(self, manual_gateway):
        result = await manual_gateway.send_sms("+1234567890", "Test message")
        assert result["status"] == "manual"
        assert "Manual SMS required" in result["message"]

    @pytest.mark.asyncio
    async def test_webhook_sends_correct_payload(self, webhook_gateway):
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await webhook_gateway.send_sms("+1234567890", "Test message")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "YOUR_SMS_WEBHOOK_URL"
            assert call_args[1]["json"]["to"] == "+1234567890"
            assert call_args[1]["json"]["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_handles_webhook_network_error(self, webhook_gateway):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            with pytest.raises(Exception):
                await webhook_gateway.send_sms("+1234567890", "Test message")


class TestReceiveSMS:
    @pytest.mark.asyncio
    async def test_receive_returns_empty_list(self, sms_gateway):
        result = await sms_gateway.receive_sms("+1234567890")
        assert result == []

    @pytest.mark.asyncio
    async def test_receive_accepts_phone_number(self, sms_gateway):
        result = await sms_gateway.receive_sms("+9876543210")
        assert isinstance(result, list)


class TestTwilioIntegration:
    @pytest.mark.asyncio
    async def test_twilio_send_returns_success(self, twilio_gateway):
        result = await twilio_gateway._send_twilio("+1234567890", "Test")
        assert result["status"] == "sent"
        assert result["provider"] == "twilio"


class TestWebhookIntegration:
    @pytest.mark.asyncio
    async def test_webhook_send_makes_http_request(self, webhook_gateway):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_gateway._send_webhook("+1234567890", "Test")
            assert result["status"] == "sent"
            assert result["provider"] == "webhook"

    @pytest.mark.asyncio
    async def test_webhook_respects_timeout(self, webhook_gateway):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            await webhook_gateway._send_webhook("+1234567890", "Test")
            mock_client.assert_called_once()
