from unittest.mock import AsyncMock, patch

import pytest

from app.services.webhook_notification_service import WebhookNotificationService


class TestWebhookNotificationService:
    @pytest.fixture
    def service(self):
        return WebhookNotificationService()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_send_webhook_success(self, mock_post, service):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        url = "http://example.com/webhook"
        result = await service.send_webhook(url, "test.event", {"id": 1})
        assert result is True
        assert mock_post.called

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_send_webhook_failure(self, mock_post, service):
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Override retries for faster test
        service.max_retries = 1
        result = await service.send_webhook("http://fail.com", "test.event", {})
        assert result is False

    @pytest.mark.asyncio
    @patch.object(WebhookNotificationService, "send_webhook", new_callable=AsyncMock)
    async def test_notify_methods(self, mock_send, service):
        from unittest.mock import ANY

        url = "http://webhook.com"

        await service.notify_verification_created("id1", "123", "serv", 1.0, url)
        mock_send.assert_called_with(url, "verification.created", ANY)

        await service.notify_sms_received("id1", "code", url)
        mock_send.assert_called_with(url, "sms.received", ANY)

        await service.notify_verification_cancelled("id1", 1.0, url)
        mock_send.assert_called_with(url, "verification.cancelled", ANY)

        await service.notify_verification_timeout("id1", url)
        mock_send.assert_called_with(url, "verification.timeout", ANY)

    @pytest.mark.asyncio
    async def test_notify_methods_no_url(self, service):
        # Should return True and not call webhook
        assert (
            await service.notify_verification_created("id1", "123", "serv", 1.0, None)
            is True
        )
