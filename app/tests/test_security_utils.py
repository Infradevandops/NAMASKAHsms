"""Tests for security utilities."""
from datetime import timedelta

import pytest

from app.utils.security import (create_access_token, generate_api_key,
                                generate_secure_id, generate_verification_code,
                                hash_password, mask_sensitive_data,
                                validate_password_strength, verify_password,
                                verify_token)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"

    # Hash password
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify incorrect password
    assert verify_password("wrong_password", hashed) is False


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


if __name__ == "__main__":
    pytest.main([__file__])
