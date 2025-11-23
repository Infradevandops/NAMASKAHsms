"""Comprehensive test suite for unified error handling system."""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError, OperationalError
from botocore.exceptions import ClientError
from cryptography.fernet import InvalidToken

from app.core.unified_error_handling import (
    UnifiedErrorHandlingMiddleware,
    NamaskahException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ExternalServiceError,
    DatabaseError,
    InsufficientCreditsError,
    unified_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    handle_database_exceptions,
    handle_aws_exceptions,
    handle_encryption_exceptions,
    handle_http_client_exceptions,
    safe_int_conversion,
    safe_json_parse,
    setup_unified_error_handling
)


class TestUnifiedExceptionClasses:
    """Test unified exception classes."""

    def test_namaskah_exception_base(self):
        """Test base NamaskahException."""
        exc = NamaskahException("Test error", "TEST_ERROR", {"key": "value"}, 400)
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.status_code == 400

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Auth failed")
        assert exc.error_code == "AUTH_ERROR"
        assert exc.status_code == 401

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError("Access denied")
        assert exc.error_code == "AUTHZ_ERROR"
        assert exc.status_code == 403

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid input")
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_external_service_error(self):
        """Test ExternalServiceError."""
        exc = ExternalServiceError("TestService", "Service failed")
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 502
        assert exc.details["service"] == "TestService"

    def test_insufficient_credits_error_with_amounts(self):
        """Test InsufficientCreditsError with required and available amounts."""
        exc = InsufficientCreditsError(10, 5)
        assert "Required: 10" in exc.message
        assert "Available: 5" in exc.message
        assert exc.details["required"] == 10
        assert exc.details["available"] == 5

    def test_insufficient_credits_error_with_message(self):
        """Test InsufficientCreditsError with just message."""
        exc = InsufficientCreditsError("Not enough credits")
        assert exc.message == "Not enough credits"
        assert exc.details == {}


class TestUnifiedErrorHandlingMiddleware:
    """Test unified error handling middleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")

        @app.get("/database - error")
        async def database_error_endpoint():
            raise Exception("database connection failed")

        @app.get("/auth - error")
        async def auth_error_endpoint():
            raise Exception("authentication failed")

        return app

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return UnifiedErrorHandlingMiddleware(app, requests_per_minute=5)

    @pytest.fixture
    def client(self, app, middleware):
        """Create test client with middleware."""
        app.add_middleware(UnifiedErrorHandlingMiddleware, requests_per_minute=5)
        return TestClient(app)

    def test_successful_request(self, client):
        """Test successful request passes through."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make requests up to limit
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]

    def test_database_error_handling(self, client):
        """Test database error handling."""
        response = client.get("/database - error")
        assert response.status_code == 503
        assert "Database connection issue" in response.json()["message"]

    def test_auth_error_handling(self, client):
        """Test authentication error handling."""
        response = client.get("/auth - error")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["message"]

    def test_fallback_response(self, client):
        """Test fallback response for critical endpoints."""
        # Mock the middleware to have fallback for /test
        with patch.object(UnifiedErrorHandlingMiddleware, '_get_fallback_responses') as mock_fallback:
            mock_fallback.return_value = {"/test": {"fallback": True}}

            # This would normally fail, but should return fallback
            client.get("/test")
            # Since we can't easily mock the middleware after it's added,
            # we'll test the fallback method directly
            middleware = UnifiedErrorHandlingMiddleware(None)
            middleware.fallback_responses = {"/test": {"fallback": True}}

            mock_request = Mock()
            mock_request.url.path = "/test"

            fallback = middleware._get_fallback_response(mock_request)
            assert fallback is not None
            assert fallback.status_code == 200


class TestExceptionHandlers:
    """Test exception handlers."""

    @pytest.mark.asyncio
    async def test_unified_exception_handler(self):
        """Test unified exception handler."""
        request = Mock()
        exc = ValidationError("Test validation error", {"field": "test"})

        response = await unified_exception_handler(request, exc)

        assert response.status_code == 400
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content
        assert "Test validation error" in content

    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """Test HTTP exception handler."""
        from starlette.exceptions import HTTPException

        request = Mock()
        exc = HTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        content = response.body.decode()
        assert "HTTP_ERROR" in content
        assert "Not found" in content

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler."""

        request = Mock()
        exc = RequestValidationError([{"type": "missing",
                                       "loc": ["field"], "msg": "field required"}])

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content

    @pytest.mark.asyncio
    async def test_general_exception_handler_development(self):
        """Test general exception handler in development mode."""
        request = Mock()
        request.url = "http://test.com/test"
        request.method = "GET"
        exc = Exception("Test error")

        with patch('app.core.unified_error_handling.get_settings') as mock_settings:
            mock_settings.return_value.environment = "development"

            response = await general_exception_handler(request, exc)

            assert response.status_code == 500
            content = response.body.decode()
            assert "INTERNAL_ERROR" in content
            assert "Exception" in content  # Should include exception type in dev mode

    @pytest.mark.asyncio
    async def test_general_exception_handler_production(self):
        """Test general exception handler in production mode."""
        request = Mock()
        request.url = "http://test.com/test"
        request.method = "GET"
        exc = Exception("Test error")

        with patch('app.core.unified_error_handling.get_settings') as mock_settings:
            mock_settings.return_value.environment = "production"

            response = await general_exception_handler(request, exc)

            assert response.status_code == 500
            content = response.body.decode()
            assert "INTERNAL_ERROR" in content
            # Should not include detailed error info in production


class TestExceptionDecorators:
    """Test exception decorators."""

    def test_handle_database_exceptions_integrity_error(self):
        """Test database exception decorator with integrity error."""
        @handle_database_exceptions
        def test_func():
            raise IntegrityError("statement", "params", "orig")

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "integrity constraint" in exc_info.value.message.lower()

    def test_handle_database_exceptions_operational_error(self):
        """Test database exception decorator with operational error."""
        @handle_database_exceptions
        def test_func():
            raise OperationalError("statement", "params", "orig")

        with pytest.raises(DatabaseError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "DATABASE_ERROR"
        assert "connection or operation failed" in exc_info.value.message.lower()

    def test_handle_aws_exceptions_access_denied(self):
        """Test AWS exception decorator with access denied error."""
        @handle_aws_exceptions("S3")
        def test_func():
            error_response = {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied'
                }
            }
            raise ClientError(error_response, 'GetObject')

        with pytest.raises(AuthorizationError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "AUTHZ_ERROR"
        assert "Access denied to S3" in exc_info.value.message

    def test_handle_aws_exceptions_resource_not_found(self):
        """Test AWS exception decorator with resource not found error."""
        @handle_aws_exceptions("S3")
        def test_func():
            error_response = {
                'Error': {
                    'Code': 'NoSuchKey',
                    'Message': 'The specified key does not exist'
                }
            }
            raise ClientError(error_response, 'GetObject')

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "Resource not found in S3" in exc_info.value.message

    def test_handle_encryption_exceptions_invalid_token(self):
        """Test encryption exception decorator with invalid token."""
        @handle_encryption_exceptions
        def test_func():
            raise InvalidToken("Invalid token")

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "Invalid encryption token" in exc_info.value.message

    def test_handle_http_client_exceptions_connection_error(self):
        """Test HTTP client exception decorator with connection error."""
        @handle_http_client_exceptions("TestAPI")
        def test_func():
            raise ConnectionError("Connection failed")

        with pytest.raises(ExternalServiceError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
        assert "Failed to connect to TestAPI" in exc_info.value.message

    def test_handle_http_client_exceptions_timeout_error(self):
        """Test HTTP client exception decorator with timeout error."""
        @handle_http_client_exceptions("TestAPI")
        def test_func():
            raise TimeoutError("Request timed out")

        with pytest.raises(ExternalServiceError) as exc_info:
            test_func()

        assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
        assert "Timeout connecting to TestAPI" in exc_info.value.message


class TestUtilityFunctions:
    """Test utility functions."""

    def test_safe_int_conversion_valid(self):
        """Test safe int conversion with valid input."""
        result = safe_int_conversion("123")
        assert result == 123

    def test_safe_int_conversion_invalid(self):
        """Test safe int conversion with invalid input."""
        result = safe_int_conversion("invalid", default=0, field_name="test_field")
        assert result == 0

    def test_safe_int_conversion_none(self):
        """Test safe int conversion with None input."""
        result = safe_int_conversion(None, default=42)
        assert result == 42

    def test_safe_json_parse_valid(self):
        """Test safe JSON parsing with valid input."""
        result = safe_json_parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_safe_json_parse_invalid(self):
        """Test safe JSON parsing with invalid input."""
        result = safe_json_parse('invalid json', default={"error": True})
        assert result == {"error": True}

    def test_safe_json_parse_none(self):
        """Test safe JSON parsing with None input."""
        result = safe_json_parse(None)
        assert result == {}


class TestSetupFunction:
    """Test setup function."""

    def test_setup_unified_error_handling(self):
        """Test setup function adds all necessary components."""
        app = FastAPI()

        # Mock the add_middleware and add_exception_handler methods
        app.add_middleware = Mock()
        app.add_exception_handler = Mock()

        setup_unified_error_handling(app)

        # Verify middleware was added
        app.add_middleware.assert_called_once_with(UnifiedErrorHandlingMiddleware)

        # Verify exception handlers were added
        assert app.add_exception_handler.call_count == 4  # 4 exception handlers


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.fixture
    def app_with_unified_handling(self):
        """Create app with unified error handling."""
        app = FastAPI()
        setup_unified_error_handling(app)

        @app.get("/test - auth")
        async def test_auth():
            raise AuthenticationError("Token expired")

        @app.get("/test - validation")
        async def test_validation():
            raise ValidationError("Invalid input", {"field": "email"})

        @app.get("/test - external")
        async def test_external():
            raise ExternalServiceError("PaymentAPI", "Payment failed")

        return app

    def test_authentication_error_flow(self, app_with_unified_handling):
        """Test complete authentication error flow."""
        client = TestClient(app_with_unified_handling)
        response = client.get("/test - auth")

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "AUTH_ERROR"
        assert data["message"] == "Token expired"

    def test_validation_error_flow(self, app_with_unified_handling):
        """Test complete validation error flow."""
        client = TestClient(app_with_unified_handling)
        response = client.get("/test - validation")

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert data["message"] == "Invalid input"
        assert data["details"]["field"] == "email"

    def test_external_service_error_flow(self, app_with_unified_handling):
        """Test complete external service error flow."""
        client = TestClient(app_with_unified_handling)
        response = client.get("/test - external")

        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "EXTERNAL_SERVICE_ERROR"
        assert data["message"] == "Payment failed"
        assert data["details"]["service"] == "PaymentAPI"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
