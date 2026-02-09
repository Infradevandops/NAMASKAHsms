"""Unit tests for webhook service"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.webhook_service import WebhookService

class TestWebhookService:
    
    @pytest.fixture
    def webhook_service(self, db_session):
        return WebhookService(db_session)
    
    def test_create_webhook(self, webhook_service, regular_user):
        """Test creating a webhook"""
        result = webhook_service.create_webhook(
            user_id=regular_user.id,
            url="https://example.com/webhook",
            events=["sms.received", "payment.success"]
        )
        assert result['success'] == True
        assert 'webhook_id' in result
        assert 'secret' in result
    
    def test_create_webhook_invalid_url(self, webhook_service, regular_user):
        """Test webhook with invalid URL"""
        result = webhook_service.create_webhook(
            user_id=regular_user.id,
            url="not-a-url",
            events=["sms.received"]
        )
        assert result['success'] == False
    
    def test_list_webhooks(self, webhook_service, regular_user):
        """Test listing user webhooks"""
        webhooks = webhook_service.list_webhooks(regular_user.id)
        assert isinstance(webhooks, list)
    
    def test_delete_webhook(self, webhook_service, regular_user):
        """Test deleting a webhook"""
        # Create first
        created = webhook_service.create_webhook(
            user_id=regular_user.id,
            url="https://example.com/webhook",
            events=["sms.received"]
        )
        webhook_id = created['webhook_id']
        
        # Delete
        result = webhook_service.delete_webhook(webhook_id, regular_user.id)
        assert result['success'] == True
    
    async def test_trigger_webhook(self, webhook_service):
        """Test triggering a webhook"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            result = await webhook_service.trigger_webhook(
                url="https://example.com/webhook",
                event="sms.received",
                data={"code": "123456"}
            )
            assert result['success'] == True
    
    async def test_trigger_webhook_timeout(self, webhook_service):
        """Test webhook timeout"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = TimeoutError()
            
            result = await webhook_service.trigger_webhook(
                url="https://example.com/webhook",
                event="sms.received",
                data={}
            )
            assert result['success'] == False
    
    def test_verify_webhook_signature(self, webhook_service):
        """Test webhook signature verification"""
        secret = "test_secret_123"
        payload = '{"event":"test"}'
        
        signature = webhook_service.generate_signature(payload, secret)
        is_valid = webhook_service.verify_signature(payload, signature, secret)
        
        assert is_valid == True
    
    def test_invalid_webhook_signature(self, webhook_service):
        """Test invalid webhook signature"""
        is_valid = webhook_service.verify_signature(
            payload='{"event":"test"}',
            signature="invalid_signature",
            secret="test_secret"
        )
        assert is_valid == False
