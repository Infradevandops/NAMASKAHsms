"""Property-based tests for TextVerified integration.

Feature: textverified-integration
Property 4: Health Check Response Format
Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
"""
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch
from datetime import datetime
import asyncio


class TestHealthCheckResponseFormatProperty:
    """Property-based tests for health check response format.
    
    Property 4: Health Check Response Format
    *For any* successful health check call, the response SHALL contain status, 
    balance (as float), and currency fields, with HTTP status 200.
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_response_contains_required_fields(self, balance):
        """Property: Health check response always contains required fields.
        
        For any balance value, the response should contain:
        - status field (string)
        - balance field (float)
        - currency field (string, always "USD")
        - timestamp field (ISO format string)
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: All required fields must be present
            assert "status" in result, "Response must contain 'status' field"
            assert "balance" in result, "Response must contain 'balance' field"
            assert "currency" in result, "Response must contain 'currency' field"
            assert "timestamp" in result, "Response must contain 'timestamp' field"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_balance_is_always_numeric(self, balance):
        """Property: Balance in response is always numeric (float).
        
        For any balance value, the returned balance should be a float.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: Balance must be numeric
            assert isinstance(result["balance"], (int, float)), \
                f"Balance must be numeric, got {type(result['balance'])}"
            assert result["balance"] == balance, \
                f"Balance value mismatch: expected {balance}, got {result['balance']}"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_status_is_operational(self, balance):
        """Property: Status is always 'operational' for successful checks.
        
        For any balance value, the status should be 'operational'.
        
        Validates: Requirements 2.1, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: Status must be 'operational'
            assert result["status"] == "operational", \
                f"Status must be 'operational', got '{result['status']}'"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_currency_is_always_usd(self, balance):
        """Property: Currency is always 'USD'.
        
        For any balance value, the currency should always be 'USD'.
        
        Validates: Requirements 2.4, 3.3
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: Currency must always be 'USD'
            assert result["currency"] == "USD", \
                f"Currency must be 'USD', got '{result['currency']}'"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_timestamp_is_valid_iso_format(self, balance):
        """Property: Timestamp is always valid ISO format.
        
        For any balance value, the timestamp should be parseable as ISO format.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: Timestamp must be valid ISO format
            try:
                datetime.fromisoformat(result["timestamp"])
            except (ValueError, TypeError) as e:
                pytest.fail(f"Timestamp is not valid ISO format: {result['timestamp']}, error: {e}")

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_response_field_types(self, balance):
        """Property: All response fields have correct types.
        
        For any balance value, all fields should have correct types:
        - status: str
        - balance: float
        - currency: str
        - timestamp: str
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: All fields must have correct types
            assert isinstance(result["status"], str), \
                f"status must be str, got {type(result['status'])}"
            assert isinstance(result["balance"], (int, float)), \
                f"balance must be numeric, got {type(result['balance'])}"
            assert isinstance(result["currency"], str), \
                f"currency must be str, got {type(result['currency'])}"
            assert isinstance(result["timestamp"], str), \
                f"timestamp must be str, got {type(result['timestamp'])}"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_no_error_field_on_success(self, balance):
        """Property: No 'error' field in successful response.
        
        For any balance value, the response should not contain an 'error' field
        when status is 'operational'.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: No error field on success
            assert "error" not in result, \
                "Successful response should not contain 'error' field"

    @given(
        balance=st.floats(
            min_value=0.0,
            max_value=1000000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    def test_health_check_balance_matches_input(self, balance):
        """Property: Returned balance matches input balance.
        
        For any balance value, the returned balance should exactly match
        the input balance.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        with patch('app.api.verification.textverified_endpoints.TextVerifiedService') as mock_service_class:
            mock_service = Mock()
            async def mock_get_health():
                return {
                    "status": "operational",
                    "balance": balance,
                    "currency": "USD",
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_service.get_health_status = mock_get_health
            mock_service_class.return_value = mock_service
            
            from app.api.verification.textverified_endpoints import textverified_health
            result = asyncio.run(textverified_health())
            
            # Property: Balance must match input
            assert result["balance"] == balance, \
                f"Balance mismatch: expected {balance}, got {result['balance']}"
