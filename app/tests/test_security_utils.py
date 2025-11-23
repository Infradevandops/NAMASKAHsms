"""Tests for security utilities."""
import pytest
from datetime import timedelta
from app.utils.security import (
    hash_password, verify_password, create_access_token, verify_token,
    generate_api_key, generate_verification_code, generate_secure_id,
    mask_sensitive_data, validate_password_strength
)


def test_password_hashing():
    """Test password hashing and verification."""

    password = generate_test_password()

    # Hash password
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify incorrect password
    assert verify_password(generate_test_password(), hashed) is False


def test_jwt_token_creation_and_verification():
    """Test JWT token creation and verification."""
    data = {"user_id": "test_user", "email": "test@example.com"}

    # Create token
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["user_id"] == "test_user"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_jwt_token_with_custom_expiry():
    """Test JWT token with custom expiry."""
    data = {"user_id": "test_user"}
    expires_delta = timedelta(minutes=30)

    token = create_access_token(data, expires_delta)
    payload = verify_token(token)

    assert payload is not None
    assert payload["user_id"] == "test_user"


def test_invalid_jwt_token():
    """Test verification of invalid JWT token."""
    invalid_token = "invalid.jwt.token"

    payload = verify_token(invalid_token)
    assert payload is None


def test_api_key_generation():
    """Test API key generation."""
    # Default length
    api_key = generate_api_key()
    assert len(api_key) == 32
    assert api_key.isalnum()

    # Custom length
    api_key_short = generate_api_key(16)
    assert len(api_key_short) == 16

    # Uniqueness
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert key1 != key2


def test_verification_code_generation():
    """Test verification code generation."""
    # Default length
    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()

    # Custom length
    code_short = generate_verification_code(4)
    assert len(code_short) == 4
    assert code_short.isdigit()


def test_secure_id_generation():
    """Test secure ID generation."""
    # Without prefix
    secure_id = generate_secure_id()
    assert len(secure_id) == 16

    # With prefix
    prefixed_id = generate_secure_id("user", 12)
    assert prefixed_id.startswith("user_")
    assert len(prefixed_id) == 17  # "user_" + 12 chars

    # Uniqueness
    id1 = generate_secure_id()
    id2 = generate_secure_id()
    assert id1 != id2


def test_mask_sensitive_data():
    """Test sensitive data masking."""
    # Email
    email = "user@example.com"
    masked = mask_sensitive_data(email)
    assert masked.startswith("user")
    assert masked.endswith(".com")
    assert "*" in masked

    # Short data
    short_data = "abc"
    masked_short = mask_sensitive_data(short_data)
    assert masked_short == "***"

    # API key
    api_key = "abcd1234efgh5678"
    masked_key = mask_sensitive_data(api_key)
    assert masked_key.startswith("abcd")
    assert masked_key.endswith("5678")


def test_password_strength_validation():
    """Test password strength validation."""
    # Strong password
    strong_password = "StrongPass123!"
    result = validate_password_strength(strong_password)
    assert result["is_valid"] is True
    assert result["score"] == 5
    assert all(result["requirements"].values())

    # Weak password
    weak_password = "weak"
    result = validate_password_strength(weak_password)
    assert result["is_valid"] is False
    assert result["score"] < 5

    # Medium password
    medium_password = "Password123"
    result = validate_password_strength(medium_password)
    assert result["requirements"]["min_length"] is True
    assert result["requirements"]["has_uppercase"] is True
    assert result["requirements"]["has_lowercase"] is True
    assert result["requirements"]["has_digit"] is True
    assert result["requirements"]["has_special"] is False


def test_password_hashing_edge_cases():
    """Test password hashing edge cases."""

    # Empty password
    empty_hash = hash_password("")
    assert empty_hash != ""
    assert verify_password("", empty_hash) is True

    # Very long password
    long_password = "a" * 1000
    long_hash = hash_password(long_password)
    assert verify_password(long_password, long_hash) is True

    # Unicode password
    unicode_password = "P@sswörd中文"
    unicode_hash = hash_password(unicode_password)
    assert verify_password(unicode_password, unicode_hash) is True

    # Special characters
    special_password = "P@$$w0rd!#%&*()_+-=[]{}|;:',.<>?/"
    special_hash = hash_password(special_password)
    assert verify_password(special_password, special_hash) is True


def test_jwt_token_expiry():
    """Test JWT token expiry."""
    data = {"user_id": "test_user"}

    # Expired token
    expired_delta = timedelta(seconds=-1)
    expired_token = create_access_token(data, expired_delta)

    payload = verify_token(expired_token)
    assert payload is None  # Should be invalid due to expiry


def test_jwt_token_tampering():
    """Test JWT token tampering detection."""
    data = {"user_id": "test_user"}
    token = create_access_token(data)

    # Tamper with token
    tampered_token = token[:-10] + "0000000000"

    payload = verify_token(tampered_token)
    assert payload is None  # Should detect tampering


def test_api_key_format():
    """Test API key format requirements."""
    api_key = generate_api_key()

    # Should be alphanumeric
    assert api_key.isalnum()

    # Should not contain special characters
    assert not any(c in api_key for c in "!@#$%^&*()")

    # Should be URL - safe
    assert "+" not in api_key
    assert "/" not in api_key


def test_verification_code_format():
    """Test verification code format requirements."""
    code = generate_verification_code()

    # Should be numeric only
    assert code.isdigit()

    # Should not contain letters
    assert not any(c.isalpha() for c in code)

    # Should not contain special characters
    assert not any(c in code for c in "!@#$%^&*()")


def test_secure_id_format():
    """Test secure ID format requirements."""
    secure_id = generate_secure_id()

    # Should be alphanumeric
    assert secure_id.isalnum()

    # Should not contain special characters (except underscore in prefixed)
    prefixed = generate_secure_id("test")
    assert prefixed.replace("_", "").isalnum()


def test_mask_sensitive_data_edge_cases():
    """Test sensitive data masking edge cases."""
    # Single character
    masked = mask_sensitive_data("a")
    assert masked == "*"

    # Two characters
    masked = mask_sensitive_data("ab")
    assert masked == "**"

    # Phone number
    phone = "+1234567890"
    masked = mask_sensitive_data(phone)
    assert masked.startswith("+1")
    assert masked.endswith("890")

    # Credit card
    card = "4532123456789010"
    masked = mask_sensitive_data(card)
    assert masked.startswith("4532")
    assert masked.endswith("9010")


def test_password_strength_requirements():
    """Test password strength requirements."""
    # Only lowercase
    result = validate_password_strength("abcdefgh")
    assert result["requirements"]["has_lowercase"] is True
    assert result["requirements"]["has_uppercase"] is False

    # Only uppercase
    result = validate_password_strength("ABCDEFGH")
    assert result["requirements"]["has_uppercase"] is True
    assert result["requirements"]["has_lowercase"] is False

    # Only digits
    result = validate_password_strength("12345678")
    assert result["requirements"]["has_digit"] is True
    assert result["requirements"]["has_uppercase"] is False

    # Only special characters
    result = validate_password_strength("!@#$%^&*")
    assert result["requirements"]["has_special"] is True
    assert result["requirements"]["has_digit"] is False


def test_password_strength_scoring():
    """Test password strength scoring."""
    # Minimum requirements met
    result = validate_password_strength("Abcd1234")
    assert result["score"] >= 3

    # All requirements met
    result = validate_password_strength("Abcd1234!@#$")
    assert result["score"] >= 4

    # Very strong password
    result = validate_password_strength("MyStr0ng!P@ssw0rd#2024")
    assert result["score"] >= 5


def test_token_payload_integrity():
    """Test JWT token payload integrity."""
    data = {
        "user_id": "user_123",
        "email": "user@example.com",
        "role": "admin",
        "permissions": ["read", "write", "delete"]
    }

    token = create_access_token(data)
    payload = verify_token(token)

    assert payload["user_id"] == data["user_id"]
    assert payload["email"] == data["email"]
    assert payload["role"] == data["role"]
    assert payload["permissions"] == data["permissions"]


def test_security_functions_thread_safety():
    """Test security functions for thread safety."""
    import threading

    results = []

    def generate_keys():
        for _ in range(10):
            results.append(generate_api_key())

    threads = [threading.Thread(target=generate_keys) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # All keys should be unique
    assert len(results) == len(set(results))


if __name__ == "__main__":
    pytest.main([__file__])
