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
    assert validate_email("test.email+tag@domain.co.uk") is True
    
    # Invalid emails
    assert validate_email("invalid-email") is False
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
    assert validate_url("not-a-url") is False
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
    assert validate_api_key_name("production-key") is True
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
    result = validate_date_range("2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z")
    assert result["is_valid"] is True
    assert result["days_diff"] > 0
    
    # Invalid range (end before start)
    result = validate_date_range("2024-01-31T00:00:00Z", "2024-01-01T00:00:00Z")
    assert result["is_valid"] is False
    
    # Invalid format
    result = validate_date_range("invalid-date", "2024-01-01")
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


if __name__ == "__main__":
    pytest.main([__file__])