"""Tests for specific exception handling improvements."""
import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from botocore.exceptions import ClientError, BotoCoreError
from cryptography.fernet import InvalidToken

from app.utils.exception_handling import (
    handle_database_exceptions,
    handle_aws_exceptions,
    handle_encryption_exceptions,
    safe_int_conversion,
    safe_json_parse,
    DatabaseError,
    EncryptionError,
    AWSServiceError,
)


class TestDatabaseExceptionHandling:
    """Test database exception handling."""

    def test_handle_database_exceptions_integrity_error(self):
        """Test handling of database integrity errors."""
        @handle_database_exceptions
        def test_func():
            raise IntegrityError("statement", "params", "orig")

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        assert "Data integrity constraint violated" in str(exc_info.value)
        assert exc_info.value.error_code == "VALIDATION_ERROR"

    def test_handle_database_exceptions_operational_error(self):
        """Test handling of database operational errors."""
        @handle_database_exceptions
        def test_func():
            raise OperationalError("statement", "params", "orig")

        with pytest.raises(DatabaseError) as exc_info:
            test_func()

        assert "Database connection or operation failed" in str(exc_info.value)
        assert exc_info.value.error_code == "DATABASE_ERROR"

    def test_handle_database_exceptions_general_sqlalchemy_error(self):
        """Test handling of general SQLAlchemy errors."""
        @handle_database_exceptions
        def test_func():
            raise SQLAlchemyError("general error")

        with pytest.raises(DatabaseError) as exc_info:
            test_func()

        assert "Database operation failed" in str(exc_info.value)


class TestAWSExceptionHandling:
    """Test AWS exception handling."""

    def test_handle_aws_exceptions_access_denied(self):
        """Test handling of AWS access denied errors."""
        @handle_aws_exceptions("S3")
        def test_func():
            error_response = {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied to resource'
                }
            }
            raise ClientError(error_response, 'GetObject')

        with pytest.raises(AuthorizationError) as exc_info:
            test_func()

        assert "Access denied to S3" in str(exc_info.value)
        assert exc_info.value.error_code == "AUTHZ_ERROR"

    def test_handle_aws_exceptions_resource_not_found(self):
        """Test handling of AWS resource not found errors."""
        @handle_aws_exceptions("SecretsManager")
        def test_func():
            error_response = {
                'Error': {
                    'Code': 'ResourceNotFoundException',
                    'Message': 'Secret not found'
                }
            }
            raise ClientError(error_response, 'GetSecretValue')

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        assert "Resource not found in SecretsManager" in str(exc_info.value)

    def test_handle_aws_exceptions_general_client_error(self):
        """Test handling of general AWS client errors."""
        @handle_aws_exceptions("DynamoDB")
        def test_func():
            error_response = {
                'Error': {
                    'Code': 'ThrottlingException',
                    'Message': 'Rate exceeded'
                }
            }
            raise ClientError(error_response, 'PutItem')

        with pytest.raises(AWSServiceError) as exc_info:
            test_func()

        assert "DynamoDB operation failed" in str(exc_info.value)

    def test_handle_aws_exceptions_botocore_error(self):
        """Test handling of BotoCore errors."""
        @handle_aws_exceptions("S3")
        def test_func():
            raise BotoCoreError()

        with pytest.raises(AWSServiceError) as exc_info:
            test_func()

        assert "S3 connection failed" in str(exc_info.value)


class TestEncryptionExceptionHandling:
    """Test encryption exception handling."""

    def test_handle_encryption_exceptions_invalid_token(self):
        """Test handling of invalid encryption tokens."""
        @handle_encryption_exceptions
        def test_func():
            raise InvalidToken("Invalid token")

        with pytest.raises(EncryptionError) as exc_info:
            test_func()

        assert "Invalid encryption token" in str(exc_info.value)
        assert exc_info.value.error_code == "ENCRYPTION_ERROR"

    def test_handle_encryption_exceptions_invalid_key_value_error(self):
        """Test handling of invalid key ValueError."""
        @handle_encryption_exceptions
        def test_func():
            raise ValueError("Invalid key format")

        with pytest.raises(EncryptionError) as exc_info:
            test_func()

        assert "Invalid encryption key" in str(exc_info.value)

    def test_handle_encryption_exceptions_other_value_error(self):
        """Test that non - encryption ValueErrors are not caught."""
        @handle_encryption_exceptions
        def test_func():
            raise ValueError("Some other error")

        with pytest.raises(ValueError):
            test_func()


class TestSafeConversions:
    """Test safe conversion utilities."""

    def test_safe_int_conversion_valid_string(self):
        """Test safe int conversion with valid string."""
        result = safe_int_conversion("123", 0, "test_field")
        assert result == 123

    def test_safe_int_conversion_invalid_string(self):
        """Test safe int conversion with invalid string."""
        result = safe_int_conversion("invalid", 42, "test_field")
        assert result == 42

    def test_safe_int_conversion_none_value(self):
        """Test safe int conversion with None value."""
        result = safe_int_conversion(None, 10, "test_field")
        assert result == 10

    def test_safe_json_parse_valid_json(self):
        """Test safe JSON parsing with valid JSON."""
        result = safe_json_parse('{"key": "value"}', {}, "test_data")
        assert result == {"key": "value"}

    def test_safe_json_parse_invalid_json(self):
        """Test safe JSON parsing with invalid JSON."""
        result = safe_json_parse('invalid json', {"default": True}, "test_data")
        assert result == {"default": True}

    def test_safe_json_parse_none_value(self):
        """Test safe JSON parsing with None value."""
        result = safe_json_parse(None, {"fallback": True}, "test_data")
        assert result == {"fallback": True}


class TestSpecificExceptionClasses:
    """Test specific exception classes."""

    def test_database_error_creation(self):
        """Test DatabaseError creation."""
        error = DatabaseError("Test message", {"detail": "test"})
        assert error.message == "Test message"
        assert error.error_code == "DATABASE_ERROR"
        assert error.details == {"detail": "test"}

    def test_encryption_error_creation(self):
        """Test EncryptionError creation."""
        error = EncryptionError("Encryption failed", {"key_id": "test"})
        assert error.message == "Encryption failed"
        assert error.error_code == "ENCRYPTION_ERROR"
        assert error.details == {"key_id": "test"}

    def test_aws_service_error_creation(self):
        """Test AWSServiceError creation."""
        error = AWSServiceError("S3", "Upload failed", {"bucket": "test"})
        assert error.message == "Upload failed"
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.details["service"] == "S3"
        assert error.details["bucket"] == "test"


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch('app.utils.exception_handling.logger') as mock:
        yield mock


class TestExceptionHandlingIntegration:
    """Integration tests for exception handling."""

    def test_database_decorator_logs_errors(self, mock_logger):
        """Test that database decorator logs errors properly."""
        @handle_database_exceptions
        def failing_func():
            raise IntegrityError("statement", "params", "orig")

        with pytest.raises(ValidationError):
            failing_func()

        mock_logger.error.assert_called_once()
        assert "Database integrity error" in mock_logger.error.call_args[0][0]

    def test_aws_decorator_logs_errors(self, mock_logger):
        """Test that AWS decorator logs errors properly."""
        @handle_aws_exceptions("TestService")
        def failing_func():
            error_response = {
                'Error': {
                    'Code': 'ServiceException',
                    'Message': 'Service error'
                }
            }
            raise ClientError(error_response, 'TestOperation')

        with pytest.raises(AWSServiceError):
            failing_func()

        mock_logger.error.assert_called_once()
        assert "AWS TestService client error" in mock_logger.error.call_args[0][0]

    def test_encryption_decorator_logs_errors(self, mock_logger):
        """Test that encryption decorator logs errors properly."""
        @handle_encryption_exceptions
        def failing_func():
            raise InvalidToken("Bad token")

        with pytest.raises(EncryptionError):
            failing_func()

        mock_logger.error.assert_called_once()
        assert "Invalid encryption token" in mock_logger.error.call_args[0][0]


class TestRealWorldScenarios:
    """Test real - world exception handling scenarios."""

    def test_preferences_database_error_handling(self):
        """Test preferences API database error handling."""
        # This would be tested with actual database operations
        # but we can test the decorator behavior
        @handle_database_exceptions
        def save_preference():
            # Simulate database constraint violation
            raise IntegrityError("UNIQUE constraint failed", None, None)

        with pytest.raises(ValidationError) as exc_info:
            save_preference()

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "Data integrity constraint violated" in str(exc_info.value)

    def test_secrets_manager_error_handling(self):
        """Test secrets manager AWS error handling."""
        @handle_aws_exceptions("SecretsManager")
        def get_secret():
            error_response = {
                'Error': {
                    'Code': 'ResourceNotFoundException',
                    'Message': 'Secrets Manager cannot find the specified secret.'
                }
            }
            raise ClientError(error_response, 'GetSecretValue')

        with pytest.raises(ValidationError) as exc_info:
            get_secret()

        assert "Resource not found in SecretsManager" in str(exc_info.value)

    def test_encryption_manager_error_handling(self):
        """Test encryption manager error handling."""
        @handle_encryption_exceptions
        def decrypt_data():
            raise InvalidToken("Invalid token provided")

        with pytest.raises(EncryptionError) as exc_info:
            decrypt_data()

        assert "Invalid encryption token" in str(exc_info.value)
        assert exc_info.value.error_code == "ENCRYPTION_ERROR"
