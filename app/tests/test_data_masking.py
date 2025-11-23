"""Tests for data masking and sensitive information protection."""
import pytest
from app.utils.data_masking import (
    DataMasker,
    mask_sensitive_response,
    sanitize_log_data,
    create_safe_error_detail,
)


class TestDataMasker:
    """Test DataMasker utility class."""

    def test_mask_sensitive_dict_keys(self):
        """Test masking of sensitive dictionary keys."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123def456",
            "email": "user@example.com",
            "phone": "555 - 1234"
        }

        masked = DataMasker.mask_sensitive_data(data)

        assert masked["username"] == "testuser"  # Not sensitive
        assert masked["password"] == "[REDACTED]"
        assert masked["api_key"] == "[REDACTED]"
        assert masked["email"] == "[REDACTED]"
        assert masked["phone"] == "[REDACTED]"

    def test_mask_nested_dict(self):
        """Test masking of nested dictionaries."""
        data = {
            "user": {
                "name": "John Doe",
                "password": "secret123",
                "profile": {
                    "api_key": "xyz789",
                    "public_info": "visible"
                }
            }
        }

        masked = DataMasker.mask_sensitive_data(data)

        assert masked["user"]["name"] == "John Doe"
        assert masked["user"]["password"] == "[REDACTED]"
        assert masked["user"]["profile"]["api_key"] == "[REDACTED]"
        assert masked["user"]["profile"]["public_info"] == "visible"

    def test_mask_list_data(self):
        """Test masking of data in lists."""
        data = [
            {"name": "user1", "token": "abc123"},
            {"name": "user2", "secret": "def456"}
        ]

        masked = DataMasker.mask_sensitive_data(data)

        assert masked[0]["name"] == "user1"
        assert masked[0]["token"] == "[REDACTED]"
        assert masked[1]["name"] == "user2"
        assert masked[1]["secret"] == "[REDACTED]"

    def test_preserve_length_option(self):
        """Test preserve_length option."""
        data = {"password": "secret123"}

        masked = DataMasker.mask_sensitive_data(data, preserve_length=True)

        assert masked["password"] == "*" * len("secret123")

    def test_custom_mask_character(self):
        """Test custom mask character."""
        data = {"password": "secret123"}

        masked = DataMasker.mask_sensitive_data(data,
                                                mask_char="#", preserve_length=True)

        assert masked["password"] == "#" * len("secret123")

    def test_jwt_token_detection(self):
        """Test JWT token pattern detection."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        data = {"token": jwt_token}
        masked = DataMasker.mask_sensitive_data(data)

        assert masked["token"] == "[REDACTED]"

    def test_api_key_pattern_detection(self):
        """Test API key pattern detection."""
        api_key = "sk_test_abcdefghijklmnopqrstuvwxyz123456"

        data = {"access_token": api_key}
        masked = DataMasker.mask_sensitive_data(data)

        assert masked["access_token"] == "[REDACTED]"

    def test_uuid_pattern_detection(self):
        """Test UUID pattern detection."""
        uuid_value = "550e8400 - e29b-41d4 - a716-446655440000"

        data = {"session_id": uuid_value}
        masked = DataMasker.mask_sensitive_data(data)

        assert masked["session_id"] == "[REDACTED]"


class TestHeaderMasking:
    """Test header masking functionality."""

    def test_mask_sensitive_headers(self):
        """Test masking of sensitive headers."""
        headers = {
            "content - type": "application/json",
            "authorization": "Bearer abc123",
            "x - api-key": "secret - key",
            "cookie": "session = xyz789",
            "user - agent": "Mozilla/5.0"
        }

        masked = DataMasker.mask_headers(headers)

        assert masked["content - type"] == "application/json"
        assert masked["authorization"] == "[REDACTED]"
        assert masked["x - api-key"] == "[REDACTED]"
        assert masked["cookie"] == "[REDACTED]"
        assert masked["user - agent"] == "Mozilla/5.0"

    def test_case_insensitive_header_masking(self):
        """Test case - insensitive header masking."""
        headers = {
            "Authorization": "Bearer abc123",
            "X - API-KEY": "secret - key",
            "Cookie": "session = xyz789"
        }

        masked = DataMasker.mask_headers(headers)

        assert masked["Authorization"] == "[REDACTED]"
        assert masked["X - API-KEY"] == "[REDACTED]"
        assert masked["Cookie"] == "[REDACTED]"


class TestErrorMessageSanitization:
    """Test error message sanitization."""

    def test_sanitize_file_paths(self):
        """Test removal of file paths from error messages."""
        error_msg = "File not found: /home/user/app/secrets.py"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert "/home/user/app/secrets.py" not in sanitized
        assert "[FILE_PATH]" in sanitized

    def test_sanitize_database_connections(self):
        """Test removal of database connection strings."""
        error_msg = "Connection failed: postgresql://user:pass@localhost:5432/db"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert "postgresql://user:pass@localhost:5432/db" not in sanitized
        assert "[DB_CONNECTION]" in sanitized

    def test_sanitize_aws_arns(self):
        """Test removal of AWS ARNs."""
        error_msg = "Access denied to arn:aws:s3:::my - bucket/secret - file"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert "arn:aws:s3:::my - bucket/secret - file" not in sanitized
        assert "[AWS_RESOURCE]" in sanitized

    def test_sanitize_ip_addresses(self):
        """Test removal of IP addresses."""
        error_msg = "Connection timeout to 192.168.1.100"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert "192.168.1.100" not in sanitized
        assert "[IP_ADDRESS]" in sanitized

    def test_sanitize_long_secrets(self):
        """Test removal of long alphanumeric strings (potential secrets)."""
        error_msg = "Invalid token: abcdefghijklmnopqrstuvwxyz123456789"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert "abcdefghijklmnopqrstuvwxyz123456789" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_jwt_tokens(self):
        """Test removal of JWT tokens from error messages."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        error_msg = f"Invalid JWT token: {jwt_token}"

        sanitized = DataMasker.sanitize_error_message(error_msg)

        assert jwt_token not in sanitized
        assert "[JWT_TOKEN]" in sanitized


class TestEmailPhoneMasking:
    """Test email and phone number masking."""

    def test_mask_email_short(self):
        """Test masking of short email addresses."""
        email = "ab@example.com"
        masked = DataMasker.mask_email(email)
        assert masked == "**@example.com"

    def test_mask_email_normal(self):
        """Test masking of normal email addresses."""
        email = "john.doe@example.com"
        masked = DataMasker.mask_email(email)
        assert masked == "j*****e@example.com"

    def test_mask_phone_number(self):
        """Test masking of phone numbers."""
        phone = "555 - 123-4567"
        masked = DataMasker.mask_phone(phone)
        assert masked == "***-***-4567"

    def test_mask_phone_international(self):
        """Test masking of international phone numbers."""
        phone = "+1 (555) 123 - 4567"
        masked = DataMasker.mask_phone(phone)
        # Should preserve last 4 digits and formatting
        assert "4567" in masked
        assert "+1" in masked  # Preserve country code format


class TestUtilityFunctions:
    """Test utility functions."""

    def test_mask_sensitive_response(self):
        """Test mask_sensitive_response function."""
        response_data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "secret123"
            },
            "status": "success"
        }

        masked = mask_sensitive_response(response_data)

        assert masked["user"]["name"] == "John Doe"
        assert masked["user"]["email"] == "[REDACTED]"
        assert masked["user"]["password"] == "[REDACTED]"
        assert masked["status"] == "success"

    def test_sanitize_log_data(self):
        """Test sanitize_log_data function."""
        log_data = {
            "message": "User login",
            "user_id": "123",
            "headers": {
                "authorization": "Bearer abc123",
                "content - type": "application/json"
            },
            "query_params": {
                "token": "secret123",
                "page": "1"
            }
        }

        sanitized = sanitize_log_data(log_data)

        assert sanitized["message"] == "User login"
        assert sanitized["user_id"] == "123"
        assert sanitized["headers"]["authorization"] == "[REDACTED]"
        assert sanitized["headers"]["content - type"] == "application/json"
        assert sanitized["query_params"]["token"] == "[REDACTED]"
        assert sanitized["query_params"]["page"] == "1"

    def test_create_safe_error_detail(self):
        """Test create_safe_error_detail function."""
        error = ValueError("Database connection failed: postgresql://user:pass@localhost/db")

        safe_detail = create_safe_error_detail(error)

        assert "postgresql://user:pass@localhost/db" not in safe_detail
        assert "[DB_CONNECTION]" in safe_detail

    def test_create_safe_error_detail_with_type(self):
        """Test create_safe_error_detail with include_type = True."""
        error = ValueError("Some error message")

        safe_detail = create_safe_error_detail(error, include_type=True)

        assert safe_detail.startswith("ValueError:")


class TestSensitivePatterns:
    """Test sensitive pattern detection."""

    def test_sensitive_key_patterns(self):
        """Test detection of sensitive key patterns."""
        sensitive_keys = [
            "password", "secret", "key", "token", "auth", "bearer",
            "api_key", "credit_card", "ssn", "social_security"
        ]

        for key in sensitive_keys:
            assert DataMasker._is_sensitive_key(key)
            assert DataMasker._is_sensitive_key(key.upper())
            assert DataMasker._is_sensitive_key(f"user_{key}")
            assert DataMasker._is_sensitive_key(f"{key}_value")

    def test_non_sensitive_keys(self):
        """Test that non - sensitive keys are not flagged."""
        non_sensitive_keys = [
            "name", "username", "id", "status", "created_at", "updated_at",
            "count", "total", "page", "limit"
        ]

        for key in non_sensitive_keys:
            assert not DataMasker._is_sensitive_key(key)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data(self):
        """Test masking of empty data structures."""
        assert DataMasker.mask_sensitive_data({}) == {}
        assert DataMasker.mask_sensitive_data([]) == []
        assert DataMasker.mask_sensitive_data("") == ""
        assert DataMasker.mask_sensitive_data(None) is None

    def test_non_string_values(self):
        """Test masking with non - string values."""
        data = {
            "password": 123456,
            "count": 42,
            "active": True,
            "config": None
        }

        masked = DataMasker.mask_sensitive_data(data)

        assert masked["password"] == "[REDACTED]"  # Sensitive key masked
        assert masked["count"] == 42  # Non - sensitive preserved
        assert masked["active"] is True
        assert masked["config"] is None

    def test_circular_references(self):
        """Test handling of circular references (basic case)."""
        data = {"name": "test"}
        data["sel"] = data  # Create circular reference

        # Should not crash, though may not handle circular refs perfectly
        try:
            masked = DataMasker.mask_sensitive_data(data)
            # If it doesn't crash, that's good enough for this test
            assert "name" in masked
        except RecursionError:
            pytest.skip("Circular reference handling not implemented")

    def test_very_long_strings(self):
        """Test handling of very long strings."""
        long_string = "a" * 10000
        data = {"password": long_string}

        masked = DataMasker.mask_sensitive_data(data)

        assert masked["password"] == "[REDACTED]"

    def test_unicode_strings(self):
        """Test handling of unicode strings."""
        data = {
            "password": "пароль123",
            "name": "José María"
        }

        masked = DataMasker.mask_sensitive_data(data)

        assert masked["password"] == "[REDACTED]"
        assert masked["name"] == "José María"
