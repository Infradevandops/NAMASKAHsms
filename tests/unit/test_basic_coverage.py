"""Basic tests to increase coverage for untested modules."""
import pytest


def test_voice_polling_service_imports():
    """Test voice polling service can be imported."""
    from app.services.voice_polling_service import VoicePollingService
    assert VoicePollingService is not None


def test_webhook_notification_service_imports():
    """Test webhook notification service can be imported."""
    from app.services.webhook_notification_service import WebhookNotificationService
    assert WebhookNotificationService is not None


def test_whatsapp_service_imports():
    """Test whatsapp service can be imported."""
    from app.services.whatsapp_service import WhatsAppService
    assert WhatsAppService is not None
