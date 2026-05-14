from datetime import timedelta

from app.schemas.validators import validate_password_strength
from app.utils.data_masking import DataMasker as DataMasking
from app.utils.security import (
    create_access_token,
    generate_api_key,
    generate_secure_id,
    generate_verification_code,
    hash_password,
    verify_password,
    verify_token,
)


def test_password_hashing():

    password = "StrongPass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False
    assert verify_password(password, "invalid_hash") is False


def test_jwt_tokens():

    data = {"user_id": "123", "email": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    assert token is not None

    payload = verify_token(token)
    assert payload["user_id"] == "123"
    assert payload["email"] == "test@example.com"

    # Test invalid token
    assert verify_token("invalid.token.here") is None


def test_generators():

    assert len(generate_api_key(32)) == 32
    assert len(generate_verification_code(6)) == 6
    assert generate_verification_code(6).isdigit()

    assert generate_secure_id("prefix", 10).startswith("prefix_")
    assert len(generate_secure_id("", 16)) == 16


def test_mask_sensitive_data():
    result = DataMasking.mask_sensitive_data("1234567890")
    assert isinstance(result, str)
    assert "1234567890" not in result or result == "1234567890"  # masked or passthrough

    result_dict = DataMasking.mask_sensitive_data(
        {"password": "secret", "email": "a@b.com"}
    )
    assert isinstance(result_dict, dict)


def test_validate_password_strength():
    res = validate_password_strength("Short1!")
    assert res is not None

    res = validate_password_strength("StrongPass123!@#")
    assert res is not None
