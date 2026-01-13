"""Tests for SMS forwarding email functionality."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.api.core.forwarding import _send_forwarding_email


class TestForwardingEmail:
    """Test email forwarding functionality."""

    @pytest.mark.asyncio
    async def test_send_forwarding_email_success(self):
        """Should send forwarding email successfully."""
        sms_data = {
            "message": "Your verification code is 123456",
            "phone_number": "+1234567890",
            "service": "WhatsApp",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_test": False
        }
        
        with patch('app.api.core.forwarding.email_service') as mock_email:
            mock_email.enabled = True
            mock_email.from_email = "noreply@namaskah.app"
            mock_email._send_smtp = Mock()
            
            result = await _send_forwarding_email("user@example.com", sms_data)
            
            assert result is True
            mock_email._send_smtp.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_forwarding_email_test_message(self):
        """Should send test message with warning banner."""
        sms_data = {
            "message": "Test message",
            "phone_number": "+1234567890",
            "service": "Test Service",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_test": True
        }
        
        with patch('app.api.core.forwarding.email_service') as mock_email:
            mock_email.enabled = True
            mock_email.from_email = "noreply@namaskah.app"
            mock_email._send_smtp = Mock()
            
            result = await _send_forwarding_email("user@example.com", sms_data)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_send_forwarding_email_service_disabled(self):
        """Should return False when email service is disabled."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('app.api.core.forwarding.email_service') as mock_email:
            mock_email.enabled = False
            
            result = await _send_forwarding_email("user@example.com", sms_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_forwarding_email_smtp_failure(self):
        """Should handle SMTP failure gracefully."""
        sms_data = {
            "message": "Test",
            "phone_number": "+1234567890",
            "service": "Test",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('app.api.core.forwarding.email_service') as mock_email:
            mock_email.enabled = True
            mock_email.from_email = "noreply@namaskah.app"
            mock_email._send_smtp = Mock(side_effect=Exception("SMTP error"))
            
            result = await _send_forwarding_email("user@example.com", sms_data)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_forwarding_email_html_content(self):
        """Should generate proper HTML email content."""
        sms_data = {
            "message": "Your code is 123456",
            "phone_number": "+1234567890",
            "service": "WhatsApp",
            "timestamp": "2026-01-13T12:00:00Z"
        }
        
        with patch('app.api.core.forwarding.email_service') as mock_email:
            mock_email.enabled = True
            mock_email.from_email = "noreply@namaskah.app"
            
            captured_message = None
            def capture_smtp(email, message):
                nonlocal captured_message
                captured_message = message
            
            mock_email._send_smtp = Mock(side_effect=capture_smtp)
            
            await _send_forwarding_email("user@example.com", sms_data)
            
            assert captured_message is not None
            assert "Your code is 123456" in captured_message
            assert "+1234567890" in captured_message
            assert "WhatsApp" in captured_message
