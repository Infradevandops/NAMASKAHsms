"""Unit tests for TextVerified health check endpoint and service.

Feature: textverified-integration
Property 4: Health Check Response Format
Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import asyncio


@pytest.fixture
def mock_textverified_client():
    """Mock TextVerified client."""
    mock_client = Mock()
    mock_client.account = Mock()
    mock_client.account.balance = 100.50
    return mock_client


@pytest.fixture
def mock_settings():
    """Mock settings with TextVerified credentials."""
    with patch('app.services.textverified_service.settings') as mock:
        mock.textverified_api_key = 'test_api_key'
        mock.textverified_email = 'test@example.com'
        yield mock


class TestTextVerifiedService:
    """Test TextVerified service health check functionality."""

    def test_get_health_status_success(self, mock_settings):
        """Test successful health check with valid credentials.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = Mock()
            mock_client.account = Mock()
            mock_client.account.balance = 100.50
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            result = asyncio.run(service.get_health_status())
            
            # Verify response structure
            assert result["status"] == "operational"
            assert result["balance"] == 100.50
            assert result["currency"] == "USD"
            assert "timestamp" in result
            assert "error" not in result

    def test_get_health_status_not_configured(self):
        """Test health check when service is not configured.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.services.textverified_service.settings') as mock_settings:
            mock_settings.textverified_api_key = None
            mock_settings.textverified_email = None
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            result = asyncio.run(service.get_health_status())
            
            # Verify error response
            assert result["status"] == "error"
            assert result["balance"] is None
            assert result["currency"] == "USD"
            assert "error" in result

    def test_get_health_status_api_error(self, mock_settings):
        """Test health check when API call fails.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = Mock()
            mock_client.account = Mock()
            mock_client.account.balance = Mock(side_effect=Exception("API Error"))
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            result = asyncio.run(service.get_health_status())
            
            # Verify error response
            assert result["status"] == "error"
            assert result["balance"] is None
            assert result["currency"] == "USD"
            assert "error" in result

    def test_get_health_status_balance_is_numeric(self, mock_settings):
        """Test that balance is returned as numeric value.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = Mock()
            mock_client.account = Mock()
            mock_client.account.balance = 50.25
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            result = asyncio.run(service.get_health_status())
            
            # Verify balance is numeric
            assert isinstance(result["balance"], float)
            assert result["balance"] == 50.25

    def test_get_health_status_includes_timestamp(self, mock_settings):
        """Test that health check includes timestamp.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.services.textverified_service.textverified') as mock_tv:
            mock_client = Mock()
            mock_client.account = Mock()
            mock_client.account.balance = 100.50
            mock_tv.TextVerified.return_value = mock_client
            
            from app.services.textverified_service import TextVerifiedService
            service = TextVerifiedService()
            result = asyncio.run(service.get_health_status())
            
            # Verify timestamp is present and valid ISO format
            assert "timestamp" in result
            # Try to parse as ISO format
            datetime.fromisoformat(result["timestamp"])


class TestHealthCheckEndpoint:
    """Test health check endpoint."""

    def test_health_check_endpoint_success(self):
        """Test health check endpoint returns 200 with valid response.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": 100.50,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Verify response
            assert result["status"] == "operational"
            assert result["balance"] == 100.50
            assert result["currency"] == "USD"

    def test_health_check_response_format(self):
        """Test health check response has correct format.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": 100.50,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Verify all required fields are present
            assert "status" in result
            assert "balance" in result
            assert "currency" in result
            assert "timestamp" in result
            
            # Verify field types
            assert isinstance(result["status"], str)
            assert isinstance(result["balance"], (int, float))
            assert isinstance(result["currency"], str)
            assert isinstance(result["timestamp"], str)


class TestHealthCheckIntegration:
    """Integration tests for health check."""

    def test_health_check_with_different_balances(self):
        """Test health check works with various balance values.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        test_balances = [0.0, 1.5, 100.50, 999.99, 10000.0]
        
        for balance in test_balances:
            with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
                mock_service = Mock()
                async def mock_get_health(b=balance):
                    return {
                        "status": "operational",
                        "balance": b,
                        "currency": "USD",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                mock_service.get_health_status = mock_get_health
                mock_service_class.return_value = mock_service
                
                from app.api.verification.textverified_endpoints import textverified_health
                result = asyncio.run(textverified_health())
                
                # Verify balance is correctly returned
                assert result["balance"] == balance
                assert isinstance(result["balance"], float)

    def test_health_check_currency_always_usd(self):
        """Test health check always returns USD currency.
        
        Validates: Requirements 2.4, 3.3
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": 100.50,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Verify currency is always USD
            assert result["currency"] == "USD"
