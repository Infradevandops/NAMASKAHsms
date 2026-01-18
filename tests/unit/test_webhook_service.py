import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.webhook_service import WebhookService

@pytest.mark.asyncio
async def test_register_webhook():
    """Test webhook registration."""
    service = WebhookService()
    user_id = "user_123"
    url = "https://example.com/webhook"
    events = ["payment.success"]
    
    webhook_id = await service.register(user_id, url, events)
    
    assert webhook_id.startswith(f"wh_{user_id}_")
    assert webhook_id in service.webhooks
    assert service.webhooks[webhook_id]["url"] == url
    assert service.webhooks[webhook_id]["events"] == events
    assert service.webhooks[webhook_id]["active"] is True

@pytest.mark.asyncio
async def test_deliver_webhook_success():
    """Test successful webhook delivery with signature."""
    service = WebhookService()
    webhook_id = await service.register("u1", "http://test.com", ["test_event"])
    secret = "my_secret_key"
    data = {"transaction_id": "tx_123"}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        
        await service.deliver(webhook_id, "test_event", data, secret)
        
        assert mock_post.called
        args, kwargs = mock_post.call_args
        
        # Verify URL
        assert args[0] == "http://test.com"
        
        # Verify Payload
        payload = json.loads(kwargs["content"])
        assert payload["event"] == "test_event"
        assert payload["data"] == data
        
        # Verify Signature Header
        headers = kwargs["headers"]
        assert "X - Webhook-Signature" in headers
        assert headers["Content - Type"] == "application/json"
        
        # Verify Signature content
        expected_sig = service._sign_payload(kwargs["content"], secret)
        assert headers["X - Webhook-Signature"] == expected_sig

@pytest.mark.asyncio
async def test_deliver_webhook_inactive_or_missing():
    """Test delivery to missing or inactive webhook."""
    service = WebhookService()
    
    # Missing ID
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await service.deliver("missing_id", "event", {}, "secret")
        assert not mock_post.called

    # Inactive
    webhook_id = await service.register("u1", "http://test.com", ["event"])
    service.webhooks[webhook_id]["active"] = False
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await service.deliver(webhook_id, "event", {}, "secret")
        assert not mock_post.called

@pytest.mark.asyncio
async def test_deliver_webhook_retry_logic():
    """Test retry logic disables webhook after failures."""
    service = WebhookService()
    webhook_id = await service.register("u1", "http://test.com", ["event"])
    
    # Simulate failures
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        # Initial state
        assert service.webhooks[webhook_id]["retries"] == 0
        assert service.webhooks[webhook_id]["active"] is True
        
        # Fail 4 times (threshold is > 3)
        for i in range(4):
            await service.deliver(webhook_id, "event", {}, "secret")
            
        # Should be active until AFTER 4th failure checks logic? 
        # Code: retries += 1. If retries > 3: active = False.
        # Call 1: retries=1
        # Call 2: retries=2
        # Call 3: retries=3
        # Call 4: retries=4 -> active=False
        
        assert service.webhooks[webhook_id]["retries"] == 4
        assert service.webhooks[webhook_id]["active"] is False
        
        # 5th call should not trigger post
        mock_post.reset_mock()
        await service.deliver(webhook_id, "event", {}, "secret")
        assert not mock_post.called
