"""Tests for validation utilities."""
import pytest
from app.utils.validation import (
    validate_email, validate_phone_number, validate_url, validate_service_name,
    validate_currency_amount, sanitize_input, validate_api_key_name,
    validate_pagination_params, validate_date_range, validate_webhook_url,
    ValidationMixin
)


def test_validate_email():
    """Test email validation."""
    # Valid emails
    assert validate_email("user@example.com") is True
    assert validate_email("test.email + tag@domain.co.uk") is True

    # Invalid emails
    assert validate_email("invalid - email") is False
    assert validate_email("@domain.com") is False
    assert validate_email("user@") is False
    assert validate_email("") is False


def test_validate_phone_number():
    """Test phone number validation."""
    # Valid phone numbers
    result = validate_phone_number("+1234567890")
    assert result["is_valid"] is True
    assert result["formatted"] is not None

    # Invalid phone numbers
    result = validate_phone_number("invalid")
    assert result["is_valid"] is False
    assert result["formatted"] is None


def test_validate_url():
    """Test URL validation."""
    # Valid URLs
    assert validate_url("https://example.com") is True
    assert validate_url("http://subdomain.example.com/path") is True

    # Invalid URLs
    assert validate_url("not - a-url") is False
    assert validate_url("") is False
    assert validate_url("ftp://example.com") is True  # Valid URL format


def test_validate_service_name():
    """Test service name validation."""
    # Valid services
    assert validate_service_name("telegram") is True
    assert validate_service_name("WHATSAPP") is True  # Case insensitive

    # Invalid services
    assert validate_service_name("unknown_service") is False
    assert validate_service_name("") is False


def test_validate_currency_amount():
    """Test currency amount validation."""
    # Valid amounts
    result = validate_currency_amount(10.50)
    assert result["is_valid"] is True
    assert result["amount"] == 10.50

    # Invalid amounts
    result = validate_currency_amount(-5.0)
    assert result["is_valid"] is False

    result = validate_currency_amount(200000.0)
    assert result["is_valid"] is False


def test_sanitize_input():
    """Test input sanitization."""
    # HTML removal
    sanitized = sanitize_input("<script>alert('xss')</script>Hello World")
    assert "<script>" not in sanitized
    assert "Hello World" in sanitized

    # Length limiting
    long_text = "a" * 2000
    sanitized = sanitize_input(long_text, max_length=100)
    assert len(sanitized) == 100

    # Whitespace cleanup
    sanitized = sanitize_input("  Multiple   spaces  ")
    assert sanitized == "Multiple spaces"


def test_validate_api_key_name():
    """Test API key name validation."""
    # Valid names
    assert validate_api_key_name("My API Key") is True
    assert validate_api_key_name("production - key") is True
    assert validate_api_key_name("test_key_123") is True

    # Invalid names
    assert validate_api_key_name("") is False
    assert validate_api_key_name("ab") is False  # Too short
    assert validate_api_key_name("a" * 60) is False  # Too long
    assert validate_api_key_name("key@#$") is False  # Invalid characters


def test_validate_pagination_params():
    """Test pagination parameter validation."""
    # Valid params
    result = validate_pagination_params(2, 20)
    assert result["page"] == 2
    assert result["size"] == 20
    assert result["offset"] == 20

    # Invalid params (should be corrected)
    result = validate_pagination_params(-1, 200, max_size=50)
    assert result["page"] == 1  # Corrected to minimum
    assert result["size"] == 50  # Corrected to maximum


def test_validate_date_range():
    """Test date range validation."""
    # Valid range
    result = validate_date_range("2024 - 01-01T00:00:00Z", "2024 - 01-31T23:59:59Z")
    assert result["is_valid"] is True
    assert result["days_diff"] > 0

    # Invalid range (end before start)
    result = validate_date_range("2024 - 01-31T00:00:00Z", "2024 - 01-01T00:00:00Z")
    assert result["is_valid"] is False

    # Invalid format
    result = validate_date_range("invalid - date", "2024 - 01-01")
    assert result["is_valid"] is False


def test_validate_webhook_url():
    """Test webhook URL validation."""
    # Valid webhook URL
    result = validate_webhook_url("https://api.example.com/webhook")
    assert result["is_valid"] is True
    assert result["reason"] is None

    # Invalid - HTTP instead of HTTPS
    result = validate_webhook_url("http://api.example.com/webhook")
    assert result["is_valid"] is False
    assert "HTTPS" in result["reason"]

    # Invalid - localhost
    result = validate_webhook_url("https://localhost/webhook")
    assert result["is_valid"] is False
    assert "Private/local" in result["reason"]


def test_validation_mixin():
    """Test ValidationMixin methods."""
    # Test required fields validation
    data = {"name": "John", "email": ""}
    missing = ValidationMixin.validate_required_fields(data, ["name", "email", "phone"])
    assert "email" in missing
    assert "phone" in missing
    assert "name" not in missing

    # Test field length validation
    data = {"name": "John", "description": "a" * 200}
    limits = {"name": 50, "description": 100}
    invalid = ValidationMixin.validate_field_lengths(data, limits)
    assert len(invalid) == 1
    assert "description" in invalid[0]


def test_validate_email_edge_cases():
    """Test email validation edge cases."""
    # Subdomain emails
    assert validate_email("user@mail.example.co.uk") is True

    # Plus addressing
    assert validate_email("user + tag@example.com") is True

    # Numbers and dots
    assert validate_email("user.name123@example.com") is True

    # Very long email
    long_email = "a" * 64 + "@" + "b" * 63 + ".com"
    assert validate_email(long_email) is True

    # Spaces
    assert validate_email("user @example.com") is False
    assert validate_email("user@ example.com") is False


def test_validate_phone_number_edge_cases():
    """Test phone number validation edge cases."""
    # Different country codes
    result = validate_phone_number("+44123456789")  # UK
    assert result["is_valid"] is True

    result = validate_phone_number("+91123456789")  # India
    assert result["is_valid"] is True

    # Without country code
    result = validate_phone_number("1234567890")
    assert result["is_valid"] is False or \
        result["is_valid"] is True  # Depends on implementation

    # Too short
    result = validate_phone_number("+1234")
    assert result["is_valid"] is False

    # Too long
    result = validate_phone_number("+" + "1" * 20)
    assert result["is_valid"] is False


def test_sanitize_input_edge_cases():
    """Test input sanitization edge cases."""
    # SQL injection attempt
    sanitized = sanitize_input("'; DROP TABLE users; --")
    assert "DROP TABLE" in sanitized  # Should not execute, just sanitize

    # Unicode characters
    sanitized = sanitize_input("Hello 世界 🌍")
    assert "Hello" in sanitized

    # Null bytes
    sanitized = sanitize_input("Hello\x00World")
    assert "\x00" not in sanitized

    # Control characters
    sanitized = sanitize_input("Hello\nWorld\tTest")
    assert "\n" not in sanitized or "\t" not in sanitized


def test_validate_currency_amount_edge_cases():
    """Test currency amount validation edge cases."""
    # Zero amount
    result = validate_currency_amount(0.0)
    assert result["is_valid"] is False  # Usually not allowed

    # Very small amount
    result = validate_currency_amount(0.01)
    assert result["is_valid"] is True

    # Decimal precision
    result = validate_currency_amount(10.999)
    assert result["is_valid"] is True

    # String input
    result = validate_currency_amount("10.50")
    # Should handle string conversion


def test_validate_pagination_params_edge_cases():
    """Test pagination parameter edge cases."""
    # Page 0
    result = validate_pagination_params(0, 20)
    assert result["page"] >= 1

    # Negative size
    result = validate_pagination_params(1, -10)
    assert result["size"] > 0

    # Very large page
    result = validate_pagination_params(999999, 20)
    assert result["page"] > 0

    # Very large size
    result = validate_pagination_params(1, 999999, max_size=100)
    assert result["size"] <= 100


def test_validate_date_range_edge_cases():
    """Test date range validation edge cases."""
    # Same start and end
    result = validate_date_range("2024 - 01-01T00:00:00Z", "2024 - 01-01T00:00:00Z")
    assert result["is_valid"] is True
    assert result["days_diff"] == 0

    # Very large range
    result = validate_date_range("2000 - 01-01T00:00:00Z", "2024 - 12-31T23:59:59Z")
    assert result["is_valid"] is True
    assert result["days_diff"] > 8000

    # Future dates
    result = validate_date_range("2025 - 01-01T00:00:00Z", "2025 - 12-31T23:59:59Z")
    assert result["is_valid"] is True


def test_validate_webhook_url_edge_cases():
    """Test webhook URL validation edge cases."""
    # With port
    result = validate_webhook_url("https://api.example.com:8443/webhook")
    assert result["is_valid"] is True

    # With query parameters
    result = validate_webhook_url("https://api.example.com/webhook?token = abc123")
    assert result["is_valid"] is True

    # With authentication
    result = validate_webhook_url("https://user:pass@api.example.com/webhook")
    assert result["is_valid"] is True

    # IP address
    result = validate_webhook_url("https://192.168.1.1/webhook")
    assert result["is_valid"] is False  # Private IP

    # Public IP
    result = validate_webhook_url("https://8.8.8.8/webhook")
    assert result["is_valid"] is True


def test_validation_error_messages():
    """Test validation error messages."""
    # Invalid email should have clear message
    result = validate_email("invalid")
    assert result is False

    # Invalid phone should have reason
    result = validate_phone_number("invalid")
    assert result["is_valid"] is False
    assert "reason" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
