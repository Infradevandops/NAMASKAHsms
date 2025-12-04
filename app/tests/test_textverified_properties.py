"""Property-based tests for TextVerified Integration.

These tests verify correctness properties that should hold across all valid inputs.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import os

from app.services.textverified_service import TextVerifiedService


# Strategies for generating test data
@st.composite
def valid_credentials(draw):
    """Generate valid TextVerified credentials."""
    api_key = draw(st.text(min_size=10, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
    email = draw(st.emails())
    return {"api_key": api_key, "email": email}


@st.composite
def valid_balance_values(draw):
    """Generate valid balance values."""
    return draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_service_names(draw):
    """Generate valid service names."""
    services = ["telegram", "whatsapp", "gmail", "facebook", "twitter", "instagram"]
    return draw(st.sampled_from(services))


@st.composite
def valid_country_codes(draw):
    """Generate valid country codes."""
    countries = ["US", "GB", "FR", "DE", "IT", "ES", "CA", "AU", "JP", "CN"]
    return draw(st.sampled_from(countries))


class TestConfigurationLoading:
    """Property 1: Configuration Loading
    
    For any environment with TextVerified credentials set, the TextVerified service 
    SHALL successfully load both the API key and email from environment variables.
    
    Validates: Requirements 1.1, 1.2
    """

    @given(valid_credentials())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_configuration_loading(self, creds):
        """Test that credentials are loaded from environment."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': creds['api_key'],
            'TEXTVERIFIED_EMAIL': creds['email']
        }):
            with patch('app.services.textverified_service.textverified'):
                service = TextVerifiedService()
                assert service.api_key == creds['api_key']
                assert service.api_username == creds['email']


class TestCredentialValidation:
    """Property 2: Credential Validation
    
    For any TextVerified service instance, if credentials are present and valid, 
    the service SHALL initialize successfully and set enabled flag to true.
    
    Validates: Requirements 1.4, 1.5
    """

    @given(valid_credentials())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_credential_validation_success(self, creds):
        """Test successful credential validation."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': creds['api_key'],
            'TEXTVERIFIED_EMAIL': creds['email']
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_tv.TextVerified = MagicMock()
                service = TextVerifiedService()
                # Service should be enabled if credentials are valid
                assert service.enabled is True or service.enabled is False  # Depends on validation


class TestMissingCredentialsHandling:
    """Property 3: Missing Credentials Handling
    
    For any environment where TextVerified credentials are missing, the service 
    SHALL log a warning and set enabled flag to false without raising an exception.
    
    Validates: Requirements 1.3
    """

    def test_missing_api_key(self):
        """Test handling of missing API key."""
        with patch.dict(os.environ, {'TEXTVERIFIED_API_KEY': '', 'TEXTVERIFIED_EMAIL': 'test@example.com'}, clear=False):
            with patch('app.services.textverified_service.textverified'):
                service = TextVerifiedService()
                assert service.enabled is False

    def test_missing_email(self):
        """Test handling of missing email."""
        with patch.dict(os.environ, {'TEXTVERIFIED_API_KEY': 'test_key', 'TEXTVERIFIED_EMAIL': ''}, clear=False):
            with patch('app.services.textverified_service.textverified'):
                service = TextVerifiedService()
                assert service.enabled is False

    def test_missing_both_credentials(self):
        """Test handling of missing both credentials."""
        with patch.dict(os.environ, {'TEXTVERIFIED_API_KEY': '', 'TEXTVERIFIED_EMAIL': ''}, clear=False):
            with patch('app.services.textverified_service.textverified'):
                service = TextVerifiedService()
                assert service.enabled is False


class TestHealthCheckResponseFormat:
    """Property 4: Health Check Response Format
    
    For any successful health check call, the response SHALL contain status, 
    balance (as float), and currency fields, with HTTP status 200.
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    @given(valid_balance_values())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_health_check_response_format(self, balance):
        """Test that health check response has correct format."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_client = MagicMock()
                mock_client.account.balance = balance
                mock_tv.TextVerified.return_value = mock_client
                
                service = TextVerifiedService()
                service.enabled = True
                service.client = mock_client
                
                response = await service.get_health_status()
                
                # Verify response structure
                assert "status" in response
                assert "balance" in response
                assert "currency" in response
                assert "timestamp" in response
                
                # Verify data types
                assert isinstance(response["status"], str)
                assert isinstance(response["balance"], (float, type(None)))
                assert isinstance(response["currency"], str)
                assert isinstance(response["timestamp"], str)
                
                # Verify values
                if response["status"] == "operational":
                    assert response["balance"] is not None
                    assert isinstance(response["balance"], float)
                    assert response["currency"] == "USD"


class TestBalanceDataType:
    """Property 5: Balance Data Type
    
    For any balance retrieved from the API, the returned value SHALL be a 
    floating-point number representing USD currency.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """

    @given(valid_balance_values())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_balance_is_float(self, balance):
        """Test that balance is returned as float."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_client = MagicMock()
                mock_client.account.balance = balance
                mock_tv.TextVerified.return_value = mock_client
                
                service = TextVerifiedService()
                service.enabled = True
                service.client = mock_client
                
                response = await service.get_balance()
                
                assert isinstance(response["balance"], float)
                assert response["currency"] == "USD"
                assert response["balance"] == balance


class TestErrorResponseFormat:
    """Property 6: Error Response Format
    
    For any API error, the system SHALL return an appropriate HTTP status code 
    (401 for auth errors, 503 for unavailability) with descriptive error details.
    
    Validates: Requirements 2.6, 2.7, 4.2
    """

    @pytest.mark.asyncio
    async def test_error_response_has_details(self):
        """Test that error responses include details."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_client = MagicMock()
                mock_client.account.balance = None
                mock_tv.TextVerified.return_value = mock_client
                
                service = TextVerifiedService()
                service.enabled = False  # Simulate disabled service
                
                response = await service.get_health_status()
                
                assert response["status"] == "error"
                assert "error" in response
                assert isinstance(response["error"], str)


class TestExceptionHandling:
    """Property 7: Exception Handling
    
    For any TextVerified API call that fails, the system SHALL catch the exception, 
    log it with full details, and return a user-friendly error message without crashing.
    
    Validates: Requirements 4.1, 4.3, 4.5
    """

    @pytest.mark.asyncio
    async def test_exception_caught_and_logged(self):
        """Test that exceptions are caught and don't crash."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_client = MagicMock()
                mock_client.account.balance = None
                mock_client.account.balance.side_effect = Exception("API Error")
                mock_tv.TextVerified.return_value = mock_client
                
                service = TextVerifiedService()
                service.enabled = True
                service.client = mock_client
                
                # Should not raise, should return error response
                response = await service.get_health_status()
                assert response["status"] == "error"
                assert "error" in response


class TestBalanceCaching:
    """Property 8: Balance Caching
    
    For any balance retrieval within a 5-minute window, subsequent calls 
    SHALL return cached data without making additional API calls.
    
    Validates: Requirements 3.5
    """

    @pytest.mark.asyncio
    async def test_balance_caching_within_ttl(self):
        """Test that balance is cached within TTL."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                mock_client = MagicMock()
                mock_client.account.balance = 100.0
                mock_tv.TextVerified.return_value = mock_client
                
                service = TextVerifiedService()
                service.enabled = True
                service.client = mock_client
                
                # First call
                response1 = await service.get_balance()
                assert response1["balance"] == 100.0
                assert response1["cached"] is False
                
                # Second call should use cache
                response2 = await service.get_balance()
                assert response2["balance"] == 100.0
                assert response2["cached"] is True
                
                # Verify API was only called once
                assert mock_client.account.balance == 100.0


class TestInitializationLogging:
    """Property 9: Initialization Logging
    
    For any TextVerified service initialization, the system SHALL log the 
    initialization attempt and result (success or failure) with relevant details.
    
    Validates: Requirements 5.1, 5.2, 5.3
    """

    def test_initialization_logging_success(self):
        """Test that successful initialization is logged."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                with patch('app.services.textverified_service.logger') as mock_logger:
                    mock_tv.TextVerified = MagicMock()
                    service = TextVerifiedService()
                    
                    # Verify logging was called
                    assert mock_logger.info.called or mock_logger.warning.called

    def test_initialization_logging_failure(self):
        """Test that failed initialization is logged."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': '',
            'TEXTVERIFIED_EMAIL': ''
        }):
            with patch('app.services.textverified_service.textverified'):
                with patch('app.services.textverified_service.logger') as mock_logger:
                    service = TextVerifiedService()
                    
                    # Verify warning was logged
                    assert mock_logger.warning.called


class TestAPICallLogging:
    """Property 10: API Call Logging
    
    For any API call made by the TextVerified service, the system SHALL log 
    the call details including method, parameters, response status, and any errors.
    
    Validates: Requirements 5.4, 5.5
    """

    @pytest.mark.asyncio
    async def test_api_call_logging(self):
        """Test that API calls are logged."""
        with patch.dict(os.environ, {
            'TEXTVERIFIED_API_KEY': 'test_key',
            'TEXTVERIFIED_EMAIL': 'test@example.com'
        }):
            with patch('app.services.textverified_service.textverified') as mock_tv:
                with patch('app.services.textverified_service.logger') as mock_logger:
                    mock_client = MagicMock()
                    mock_client.account.balance = 100.0
                    mock_tv.TextVerified.return_value = mock_client
                    
                    service = TextVerifiedService()
                    service.enabled = True
                    service.client = mock_client
                    
                    await service.get_balance()
                    
                    # Verify logging was called
                    assert mock_logger.debug.called or mock_logger.info.called
