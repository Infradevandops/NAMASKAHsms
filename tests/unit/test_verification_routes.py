"""Tests for consolidated verification endpoint."""

from app.schemas.verification import VerificationCreate
from app.utils.data_masking import create_safe_error_detail


def test_verification_create_model():
    """Test VerificationCreate model validation."""
    data = VerificationCreate(service="whatsapp", country="US")
    assert data.service == "whatsapp"
    assert data.country == "US"
    assert data.capability == "sms"


def test_verification_create_defaults():
    """Test VerificationCreate with default values."""
    data = VerificationCreate(service="telegram")
    assert data.service == "telegram"
    assert data.country == "US"
    assert data.capability == "sms"


def test_create_safe_error_detail():
    """Test error detail truncation."""
    short_error = "Short error"
    assert create_safe_error_detail(Exception(short_error)) == short_error

    long_error = "x" * 150
    result = create_safe_error_detail(Exception(long_error))
    assert result == "[REDACTED]"
