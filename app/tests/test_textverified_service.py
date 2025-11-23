"""Tests for TextVerified SMS service integration."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.textverified_service import TextVerifiedService


@pytest.fixture
def textverified_service():
    """Create TextVerified service instance."""
    return TextVerifiedService()


@pytest.mark.asyncio
async def test_get_balance_success(textverified_service):
    """Test successful balance retrieval."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"balance": 100.50}

        result = await textverified_service.get_balance()

        assert result["balance"] == 100.50
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_balance_api_error(textverified_service):
    """Test balance retrieval with API error."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        with pytest.raises(TextVerifiedAPIError):
            await textverified_service.get_balance()


@pytest.mark.asyncio
async def test_buy_number_success(textverified_service):
    """Test successful number purchase."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "phone_number": "+1234567890",
            "activation_id": "12345",
            "cost": 0.50
        }

        result = await textverified_service.buy_number(country="US", service="telegram")

        assert result["phone_number"] == "+1234567890"
        assert result["activation_id"] == "12345"
        assert result["cost"] == 0.50


@pytest.mark.asyncio
async def test_buy_number_insufficient_balance(textverified_service):
    """Test number purchase with insufficient balance."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("Insufficient balance")

        with pytest.raises(TextVerifiedAPIError):
            await textverified_service.buy_number(country="US", service="telegram")


@pytest.mark.asyncio
async def test_get_sms_success(textverified_service):
    """Test successful SMS retrieval."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"sms": "123456"}

        result = await textverified_service.get_sms("12345")

        assert result == "123456"


@pytest.mark.asyncio
async def test_get_sms_not_received(textverified_service):
    """Test SMS retrieval when SMS not yet received."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = None

        result = await textverified_service.get_sms("12345")

        assert result is None


@pytest.mark.asyncio
async def test_get_sms_api_error(textverified_service):
    """Test SMS retrieval with API error."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        with pytest.raises(TextVerifiedAPIError):
            await textverified_service.get_sms("12345")


@pytest.mark.asyncio
async def test_cancel_activation_success(textverified_service):
    """Test successful activation cancellation."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"status": "cancelled"}

        result = await textverified_service.cancel_activation("12345")

        assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_retry_logic_on_failure(textverified_service):
    """Test retry logic on API failure."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            Exception("Temporary error"),
            {"balance": 100.50}
        ]

        # Should retry and succeed on second attempt
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await textverified_service.get_balance()
            assert result["balance"] == 100.50


@pytest.mark.asyncio
async def test_rate_limiting(textverified_service):
    """Test rate limiting handling."""
    with patch.object(textverified_service,
                      '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("Rate limited")

        with pytest.raises(TextVerifiedAPIError):
            await textverified_service.buy_number(country="US", service="telegram")


def test_service_initialization():
    """Test service initialization."""
    service = TextVerifiedService()
    assert service is not None
    assert hasattr(service, 'get_balance')
    assert hasattr(service, 'buy_number')
    assert hasattr(service, 'get_sms')
    assert hasattr(service, 'cancel_activation')
