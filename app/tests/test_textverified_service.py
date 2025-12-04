"""Tests for TextVerified SMS service integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os


@pytest.fixture
def mock_textverified_service():
    """Create mocked TextVerified service instance."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            mock_client.account.balance = 100.50
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            yield service


@pytest.mark.asyncio
async def test_get_balance_success(mock_textverified_service):
    """Test successful balance retrieval."""
    result = await mock_textverified_service.get_balance()
    
    assert result["balance"] == 100.50
    assert result["currency"] == "USD"


@pytest.mark.asyncio
async def test_get_balance_api_error():
    """Test balance retrieval with API error."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            type(mock_client.account).balance = property(lambda self: (_ for _ in ()).throw(Exception("API Error")))
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            with pytest.raises(Exception):
                await service.get_balance()


@pytest.mark.asyncio
async def test_buy_number_success():
    """Test successful number purchase."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_verification = MagicMock()
            mock_verification.id = "12345"
            mock_verification.number = "1234567890"
            mock_verification.total_cost = 0.50
            
            mock_client = MagicMock()
            mock_client.verifications.create.return_value = mock_verification
            mock_tv.TextVerified.return_value = mock_client
            mock_tv.ReservationCapability.SMS = "sms"
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            result = await service.buy_number(country="US", service="telegram")
            
            assert result["phone_number"] == "+11234567890"
            assert result["activation_id"] == "12345"
            assert result["cost"] == 0.50


@pytest.mark.asyncio
async def test_buy_number_insufficient_balance():
    """Test number purchase with insufficient balance."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            mock_client.verifications.create.side_effect = Exception("Insufficient balance")
            mock_tv.TextVerified.return_value = mock_client
            mock_tv.ReservationCapability.SMS = "sms"
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            with pytest.raises(Exception):
                await service.buy_number(country="US", service="telegram")


@pytest.mark.asyncio
async def test_get_sms_success():
    """Test successful SMS retrieval."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_sms = MagicMock()
            mock_sms.message = "123456"
            
            mock_verification = MagicMock()
            mock_verification.sms = [mock_sms]
            
            mock_client = MagicMock()
            mock_client.verifications.details.return_value = mock_verification
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            result = await service.get_sms("12345")
            
            assert result == "123456"


@pytest.mark.asyncio
async def test_get_sms_not_received():
    """Test SMS retrieval when SMS not yet received."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_verification = MagicMock()
            mock_verification.sms = []
            
            mock_client = MagicMock()
            mock_client.verifications.details.return_value = mock_verification
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            result = await service.get_sms("12345")
            
            assert result is None


@pytest.mark.asyncio
async def test_get_sms_api_error():
    """Test SMS retrieval with API error - returns None gracefully."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            mock_client.verifications.details.side_effect = Exception("API Error")
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            # get_sms returns None on error (graceful degradation)
            result = await service.get_sms("12345")
            assert result is None


@pytest.mark.asyncio
async def test_cancel_activation_success():
    """Test successful activation cancellation."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            mock_client.verifications.cancel.return_value = None
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            result = await service.cancel_activation("12345")
            
            assert result is True


@pytest.mark.asyncio
async def test_cancel_activation_failure():
    """Test activation cancellation failure."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = MagicMock()
            mock_client.verifications.cancel.side_effect = Exception("Cancel failed")
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            service.enabled = True
            service.client = mock_client
            
            result = await service.cancel_activation("12345")
            
            assert result is False


@pytest.mark.asyncio
async def test_balance_caching(mock_textverified_service):
    """Test that balance is cached."""
    # First call - should fetch from API
    result1 = await mock_textverified_service.get_balance()
    assert result1["cached"] is False
    
    # Second call - should use cache
    result2 = await mock_textverified_service.get_balance()
    assert result2["cached"] is True
    assert result2["balance"] == result1["balance"]


def test_service_initialization():
    """Test service initialization."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': 'test_api_key',
        'TEXTVERIFIED_EMAIL': 'test@example.com'
    }):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_tv.TextVerified = MagicMock()
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            assert service is not None
            assert hasattr(service, 'get_balance')
            assert hasattr(service, 'buy_number')
            assert hasattr(service, 'get_sms')
            assert hasattr(service, 'cancel_activation')
            assert hasattr(service, 'get_health_status')


def test_service_disabled_without_credentials():
    """Test service is disabled without credentials."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': '',
        'TEXTVERIFIED_EMAIL': ''
    }, clear=False):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            assert service.enabled is False


@pytest.mark.asyncio
async def test_health_status_when_enabled(mock_textverified_service):
    """Test health status when service is enabled."""
    result = await mock_textverified_service.get_health_status()
    
    assert result["status"] == "operational"
    assert result["balance"] == 100.50
    assert result["currency"] == "USD"
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_health_status_when_disabled():
    """Test health status when service is disabled."""
    with patch.dict(os.environ, {
        'TEXTVERIFIED_API_KEY': '',
        'TEXTVERIFIED_EMAIL': ''
    }, clear=False):
        with patch('app.services.textverified_service.textverified') as mock_tv:
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            
            result = await service.get_health_status()
            
            assert result["status"] == "error"
            assert result["error"] == "TextVerified not configured"
            assert result["balance"] is None
