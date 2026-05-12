"""Unit tests for WebhookService."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.webhook_service import WebhookService


@pytest.fixture
def webhook_service():
    return WebhookService()


@pytest.fixture
def mock_user_id():
    return "user123"


class TestCreateWebhook:
    def test_creates_webhook_successfully(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/webhook", ["payment.success"]
        )
        assert result["success"] is True
        assert "webhook_id" in result
        assert "secret" in result
        assert result["webhook_id"].startswith("wh_")

    def test_rejects_invalid_url_without_protocol(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id, "example.com/webhook", ["payment.success"]
        )
        assert result["success"] is False
        assert "Invalid URL" in result["error"]

    def test_accepts_http_url(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id, "http://localhost:8000/webhook", ["payment.success"]
        )
        assert result["success"] is True

    def test_stores_webhook_data(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id,
            "https://example.com/webhook",
            ["payment.success", "sms.received"],
        )
        webhook_id = result["webhook_id"]
        webhook = webhook_service.webhooks[webhook_id]
        assert webhook["user_id"] == mock_user_id
        assert webhook["url"] == "https://example.com/webhook"
        assert webhook["events"] == ["payment.success", "sms.received"]
        assert webhook["active"] is True
        assert webhook["retries"] == 0


class TestListWebhooks:
    def test_lists_user_webhooks(self, webhook_service, mock_user_id):
        webhook_service.create_webhook(
            mock_user_id, "https://example.com/wh1", ["event1"]
        )
        webhook_service.create_webhook(
            mock_user_id, "https://example.com/wh2", ["event2"]
        )
        webhooks = webhook_service.list_webhooks(mock_user_id)
        assert len(webhooks) == 2
        assert all("id" in wh for wh in webhooks)

    def test_excludes_secret_from_list(self, webhook_service, mock_user_id):
        webhook_service.create_webhook(
            mock_user_id, "https://example.com/wh", ["event1"]
        )
        webhooks = webhook_service.list_webhooks(mock_user_id)
        assert "secret" not in webhooks[0]

    def test_returns_empty_for_user_without_webhooks(self, webhook_service):
        webhooks = webhook_service.list_webhooks("nonexistent_user")
        assert webhooks == []

    def test_filters_by_user_id(self, webhook_service):
        webhook_service.create_webhook("user1", "https://example.com/wh1", ["event1"])
        webhook_service.create_webhook("user2", "https://example.com/wh2", ["event2"])
        webhooks = webhook_service.list_webhooks("user1")
        assert len(webhooks) == 1


class TestDeleteWebhook:
    def test_deletes_webhook_successfully(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/wh", ["event1"]
        )
        webhook_id = result["webhook_id"]
        delete_result = webhook_service.delete_webhook(webhook_id, mock_user_id)
        assert delete_result["success"] is True
        assert webhook_id not in webhook_service.webhooks

    def test_rejects_delete_for_wrong_user(self, webhook_service):
        result = webhook_service.create_webhook(
            "user1", "https://example.com/wh", ["event1"]
        )
        webhook_id = result["webhook_id"]
        delete_result = webhook_service.delete_webhook(webhook_id, "user2")
        assert delete_result["success"] is False
        assert "Not found" in delete_result["error"]

    def test_rejects_delete_for_nonexistent_webhook(
        self, webhook_service, mock_user_id
    ):
        delete_result = webhook_service.delete_webhook("nonexistent_id", mock_user_id)
        assert delete_result["success"] is False


class TestSignatureGeneration:
    def test_generates_signature(self, webhook_service):
        payload = '{"event": "test", "data": {}}'
        secret = "test_secret"
        signature = webhook_service.generate_signature(payload, secret)
        assert isinstance(signature, str)
        assert len(signature) == 64

    def test_same_payload_generates_same_signature(self, webhook_service):
        payload = '{"event": "test"}'
        secret = "secret123"
        sig1 = webhook_service.generate_signature(payload, secret)
        sig2 = webhook_service.generate_signature(payload, secret)
        assert sig1 == sig2

    def test_different_payload_generates_different_signature(self, webhook_service):
        secret = "secret123"
        sig1 = webhook_service.generate_signature('{"event": "test1"}', secret)
        sig2 = webhook_service.generate_signature('{"event": "test2"}', secret)
        assert sig1 != sig2

    def test_different_secret_generates_different_signature(self, webhook_service):
        payload = '{"event": "test"}'
        sig1 = webhook_service.generate_signature(payload, "secret1")
        sig2 = webhook_service.generate_signature(payload, "secret2")
        assert sig1 != sig2


class TestSignatureVerification:
    def test_verifies_valid_signature(self, webhook_service):
        payload = '{"event": "test"}'
        secret = "secret123"
        signature = webhook_service.generate_signature(payload, secret)
        assert webhook_service.verify_signature(payload, signature, secret) is True

    def test_rejects_invalid_signature(self, webhook_service):
        payload = '{"event": "test"}'
        secret = "secret123"
        invalid_signature = "invalid_signature_hash"
        assert (
            webhook_service.verify_signature(payload, invalid_signature, secret)
            is False
        )

    def test_rejects_signature_with_wrong_secret(self, webhook_service):
        payload = '{"event": "test"}'
        signature = webhook_service.generate_signature(payload, "secret1")
        assert webhook_service.verify_signature(payload, signature, "secret2") is False


class TestTriggerWebhook:
    @pytest.mark.asyncio
    async def test_triggers_webhook_successfully(self, webhook_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_service.trigger_webhook(
                "https://example.com/webhook", "payment.success", {"amount": 100}
            )
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_handles_webhook_failure(self, webhook_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_service.trigger_webhook(
                "https://example.com/webhook", "payment.success", {"amount": 100}
            )
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_handles_network_error(self, webhook_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await webhook_service.trigger_webhook(
                "https://example.com/webhook", "payment.success", {"amount": 100}
            )
            assert result["success"] is False
            assert "error" in result


class TestDeliverWebhook:
    @pytest.mark.asyncio
    async def test_delivers_webhook_for_subscribed_event(
        self, webhook_service, mock_user_id
    ):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/webhook", ["payment.success"]
        )
        webhook_id = result["webhook_id"]
        secret = result["secret"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            await webhook_service.deliver(
                webhook_id, "payment.success", {"amount": 100}, secret
            )
            assert webhook_service.webhooks[webhook_id]["retries"] == 0

    @pytest.mark.asyncio
    async def test_skips_delivery_for_unsubscribed_event(
        self, webhook_service, mock_user_id
    ):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/webhook", ["payment.success"]
        )
        webhook_id = result["webhook_id"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock()
            await webhook_service.deliver(
                webhook_id, "sms.received", {"code": "123"}, "secret"
            )
            mock_client.return_value.__aenter__.return_value.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_increments_retries_on_failure(self, webhook_service, mock_user_id):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/webhook", ["payment.success"]
        )
        webhook_id = result["webhook_id"]
        secret = result["secret"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            await webhook_service.deliver(
                webhook_id, "payment.success", {"amount": 100}, secret
            )
            assert webhook_service.webhooks[webhook_id]["retries"] == 1

    @pytest.mark.asyncio
    async def test_deactivates_webhook_after_max_retries(
        self, webhook_service, mock_user_id
    ):
        result = webhook_service.create_webhook(
            mock_user_id, "https://example.com/webhook", ["payment.success"]
        )
        webhook_id = result["webhook_id"]
        secret = result["secret"]
        webhook_service.webhooks[webhook_id]["retries"] = 3

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            await webhook_service.deliver(
                webhook_id, "payment.success", {"amount": 100}, secret
            )
            assert webhook_service.webhooks[webhook_id]["active"] is False


class TestRegisterWebhook:
    @pytest.mark.asyncio
    async def test_registers_webhook(self, webhook_service, mock_user_id):
        webhook_id = await webhook_service.register(
            mock_user_id, "https://example.com/webhook", ["event1", "event2"]
        )
        assert webhook_id.startswith("wh_")
        assert webhook_id in webhook_service.webhooks
        assert (
            webhook_service.webhooks[webhook_id]["url"] == "https://example.com/webhook"
        )
        assert webhook_service.webhooks[webhook_id]["events"] == ["event1", "event2"]
        assert webhook_service.webhooks[webhook_id]["active"] is True
