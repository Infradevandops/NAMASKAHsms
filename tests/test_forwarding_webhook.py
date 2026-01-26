"""Tests for SMS forwarding webhook functionality."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.api.core.forwarding import _send_forwarding_webhook


class TestForwardingWebhook:
    """Test webhook forwarding functionality."""

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_success(self):
        """Should send webhook successfully."""
        sms_data = {
            "message": "Your verification code is 123456",
            "phone_number": "+1234567890",
            "service": "WhatsApp",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_with_signature(self):
        """Should include signature header when secret provided."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        mock_response = Mock()
        mock_response.status_code = 200

        captured_headers = None

        async def capture_post(url, content, headers):
            nonlocal captured_headers
            captured_headers = headers
            return mock_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = capture_post

            result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert result is True
            assert captured_headers is not None
            assert "X-Webhook-Signature" in captured_headers
            assert "X-Webhook-Signature-Algorithm" in captured_headers
            assert captured_headers["X-Webhook-Signature-Algorithm"] == "sha256"

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_without_secret(self):
        """Should work without signature when no secret provided."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await _send_forwarding_webhook("https://example.com/webhook", None, sms_data)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_retry_on_failure(self):
        """Should retry on failure with exponential backoff."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # First two attempts fail, third succeeds
        mock_responses = [
            Mock(status_code=500),
            Mock(status_code=500),
            Mock(status_code=200),
        ]

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            response = mock_responses[call_count]
            call_count += 1
            return response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert result is True
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_timeout(self):
        """Should handle timeout gracefully."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_request_error(self):
        """Should handle request errors gracefully."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.RequestError("Connection error")
            )

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_accepted_status_codes(self):
        """Should accept various success status codes."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for status_code in [200, 201, 202, 204]:
            mock_response = Mock()
            mock_response.status_code = status_code

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

                result = await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

                assert result is True

    @pytest.mark.asyncio
    async def test_send_forwarding_webhook_payload_structure(self):
        """Should send properly structured payload."""
        sms_data = {
            "message": "Test message",
            "phone_number": "+1234567890",
            "service": "WhatsApp",
            "timestamp": "2026-01-13T12:00:00Z",
        }

        mock_response = Mock()
        mock_response.status_code = 200

        captured_content = None

        async def capture_post(url, content, headers):
            nonlocal captured_content
            captured_content = content
            return mock_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = capture_post

            await _send_forwarding_webhook("https://example.com/webhook", "secret123", sms_data)

            assert captured_content is not None
            import json

            payload = json.loads(captured_content)
            assert payload["event"] == "sms.received"
            assert "timestamp" in payload
            assert payload["data"] == sms_data
