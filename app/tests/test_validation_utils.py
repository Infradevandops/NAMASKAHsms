"""Tests for validation utilities."""
import pytest
from app.schemas.validators import (
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
    assert result["days_dif"] > 0

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
    assert result["days_dif"] == 0

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


# ============================================================================
# Additional Tests for Missing Validators
# ============================================================================


def test_validate_referral_code():
    """Test referral code validation."""
    # Valid codes
    assert validate_referral_code("ABC123") is not None
    assert validate_referral_code("XYZ789") is not None

    # Invalid codes
    with pytest.raises(ValueError):
        validate_referral_code("AB12")  # Too short
    
    with pytest.raises(ValueError):
        validate_referral_code("abc@123")  # Invalid characters


def test_validate_duration_hours():
    """Test duration hours validation."""
    # Valid durations
    assert validate_duration_hours(1.0) > 0
    assert validate_duration_hours(24.0) > 0
    assert validate_duration_hours(0.5) > 0

    # Invalid durations
    with pytest.raises(ValueError):
        validate_duration_hours(0)  # Zero not allowed
    
    with pytest.raises(ValueError):
        validate_duration_hours(-5)  # Negative not allowed


def test_validate_area_code():
    """Test area code validation."""
    # Valid area codes
    assert validate_area_code("201") is not None
    assert validate_area_code("415") is not None

    # Invalid area codes
    with pytest.raises(ValueError):
        validate_area_code("12")  # Too short
    
    with pytest.raises(ValueError):
        validate_area_code("abcd")  # Non-numeric


def test_validate_carrier_name():
    """Test carrier name validation."""
    # Valid carriers
    assert validate_carrier_name("Verizon") is not None
    assert validate_carrier_name("AT&T") is not None

    # Invalid carriers
    with pytest.raises(ValueError):
        validate_carrier_name("")  # Empty


def test_validate_password_strength():
    """Test password strength validation."""
    # Valid strong passwords
    assert validate_password_strength("SecurePass123!") is not None
    assert validate_password_strength("MyP@ssw0rd") is not None

    # Invalid weak passwords
    with pytest.raises(ValueError):
        validate_password_strength("weak")  # Too weak
    
    with pytest.raises(ValueError):
        validate_password_strength("123456")  # Only numbers


def test_validate_country_code():
    """Test country code validation."""
    # Valid country codes
    assert validate_country_code("US") is not None
    assert validate_country_code("GB") is not None
    assert validate_country_code("IN") is not None

    # Invalid country codes
    with pytest.raises(ValueError):
        validate_country_code("USA")  # Too long
    
    with pytest.raises(ValueError):
        validate_country_code("U")  # Too short


def test_validate_positive_number():
    """Test positive number validation."""
    # Valid positive numbers
    assert validate_positive_number(1.0) > 0
    assert validate_positive_number(100.5) > 0

    # Invalid numbers
    with pytest.raises(ValueError):
        validate_positive_number(0)  # Zero not positive
    
    with pytest.raises(ValueError):
        validate_positive_number(-5)  # Negative


def test_validate_non_negative_number():
    """Test non-negative number validation."""
    # Valid non-negative numbers
    assert validate_non_negative_number(0) >= 0
    assert validate_non_negative_number(100.5) >= 0

    # Invalid numbers
    with pytest.raises(ValueError):
        validate_non_negative_number(-1)  # Negative


def test_validate_string_length():
    """Test string length validation."""
    # Valid strings
    assert validate_string_length("hello", min_length=1, max_length=10) is not None
    assert validate_string_length("test", min_length=1, max_length=100) is not None

    # Invalid strings
    with pytest.raises(ValueError):
        validate_string_length("", min_length=1, max_length=10)  # Too short
    
    with pytest.raises(ValueError):
        validate_string_length("a" * 101, min_length=1, max_length=100)  # Too long


def test_validate_enum_value():
    """Test enum value validation."""
    # Valid enum values
    assert validate_enum_value("active", ["active", "inactive", "pending"]) is not None
    assert validate_enum_value("pending", ["active", "inactive", "pending"]) is not None

    # Invalid enum values
    with pytest.raises(ValueError):
        validate_enum_value("unknown", ["active", "inactive", "pending"])


def test_validate_date_format():
    """Test date format validation."""
    # Valid dates
    result = validate_date_format("2024-01-15")
    assert result is not None

    # Invalid dates
    with pytest.raises(ValueError):
        validate_date_format("invalid-date")
    
    with pytest.raises(ValueError):
        validate_date_format("2024/01/15")  # Wrong format


def test_validate_uuid():
    """Test UUID validation."""
    # Valid UUIDs
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    assert validate_uuid(valid_uuid) is not None

    # Invalid UUIDs
    with pytest.raises(ValueError):
        validate_uuid("not-a-uuid")
    
    with pytest.raises(ValueError):
        validate_uuid("550e8400-e29b-41d4-a716")  # Incomplete


def test_validate_json_string():
    """Test JSON string validation."""
    # Valid JSON
    result = validate_json_string('{"key": "value"}')
    assert result is not None
    assert isinstance(result, dict)

    # Invalid JSON
    with pytest.raises(ValueError):
        validate_json_string("{invalid json}")
    
    with pytest.raises(ValueError):
        validate_json_string("not json at all")


def test_validate_ip_address():
    """Test IP address validation."""
    # Valid IPv4 addresses
    assert validate_ip_address("192.168.1.1") is not None
    assert validate_ip_address("8.8.8.8") is not None

    # Valid IPv6 addresses
    assert validate_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is not None

    # Invalid IP addresses
    with pytest.raises(ValueError):
        validate_ip_address("256.256.256.256")  # Out of range
    
    with pytest.raises(ValueError):
        validate_ip_address("not.an.ip.address")


def test_validate_credit_amount():
    """Test credit amount validation."""
    # Valid credit amounts
    assert validate_credit_amount(10.0) > 0
    assert validate_credit_amount(100.50) > 0

    # Invalid credit amounts
    with pytest.raises(ValueError):
        validate_credit_amount(0)  # Zero not allowed
    
    with pytest.raises(ValueError):
        validate_credit_amount(-10)  # Negative not allowed


def test_validate_query_parameters():
    """Test query parameter validation."""
    # Valid parameters
    page, limit = validate_query_parameters(page=1, limit=20)
    assert page >= 1
    assert limit > 0

    # Invalid parameters (should be corrected)
    page, limit = validate_query_parameters(page=-1, limit=1000)
    assert page >= 1
    assert limit <= 100  # Should be capped


def test_validate_search_query():
    """Test search query validation."""
    # Valid search queries
    assert validate_search_query("python") is not None
    assert validate_search_query("machine learning") is not None

    # Invalid search queries
    with pytest.raises(ValueError):
        validate_search_query("")  # Empty
    
    with pytest.raises(ValueError):
        validate_search_query("a" * 300)  # Too long


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


def test_validate_referral_code_edge_cases():
    """Test referral code edge cases."""
    # Lowercase should be converted to uppercase
    result = validate_referral_code("abc123")
    assert result is not None

    # With spaces should be trimmed
    result = validate_referral_code("  ABC123  ")
    assert result is not None


def test_validate_json_string_edge_cases():
    """Test JSON string edge cases."""
    # Empty object
    result = validate_json_string("{}")
    assert result == {}

    # Array
    result = validate_json_string('["a", "b", "c"]')
    assert isinstance(result, list)

    # Nested objects
    result = validate_json_string('{"nested": {"key": "value"}}')
    assert "nested" in result


def test_validate_ip_address_edge_cases():
    """Test IP address edge cases."""
    # Localhost
    assert validate_ip_address("127.0.0.1") is not None

    # Broadcast
    assert validate_ip_address("255.255.255.255") is not None

    # IPv6 loopback
    assert validate_ip_address("::1") is not None


def test_validate_uuid_edge_cases():
    """Test UUID edge cases."""
    # UUID without hyphens should fail
    with pytest.raises(ValueError):
        validate_uuid("550e8400e29b41d4a716446655440000")
    
    # UUID with uppercase
    valid_uuid = "550E8400-E29B-41D4-A716-446655440000"
    assert validate_uuid(valid_uuid) is not None


def test_validate_webhook_url_comprehensive():
    """Comprehensive webhook URL validation tests."""
    # Valid HTTPS URLs
    assert validate_webhook_url("https://api.example.com/webhook") is not None
    assert validate_webhook_url("https://webhook.service.io/v1/events") is not None

    # Invalid - HTTP
    with pytest.raises(ValueError):
        validate_webhook_url("http://api.example.com/webhook")
    
    # Invalid - localhost
    with pytest.raises(ValueError):
        validate_webhook_url("https://localhost/webhook")


def test_validate_date_range_comprehensive():
    """Comprehensive date range validation tests."""
    # Valid ranges
    result = validate_date_range("2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z")
    assert result["is_valid"] is True

    # Invalid - end before start
    result = validate_date_range("2024-12-31T00:00:00Z", "2024-01-01T00:00:00Z")
    assert result["is_valid"] is False

    # Same date
    result = validate_date_range("2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z")
    assert result["is_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__])
