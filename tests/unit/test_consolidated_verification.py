"""Tests for consolidated verification endpoint."""

from unittest.mock import Mock

import pytest

from app.api.verification.consolidated_verification import (
    VerificationCreate,
    create_safe_error_detail,
)


def test_verification_create_model():
    """Test VerificationCreate model validation."""
    data = VerificationCreate(service_name="whatsapp", country="US", area_code="212")
    assert data.service_name == "whatsapp"
    assert data.country == "US"
    assert data.capability == "sms"
    assert data.area_code == "212"


def test_verification_create_defaults():
    """Test VerificationCreate with default values."""
    data = VerificationCreate(service_name="telegram")
    assert data.country == "US"
    assert data.capability == "sms"
    assert data.area_code is None
    assert data.carrier is None


def test_create_safe_error_detail():
    """Test error detail truncation."""
    short_error = "Short error"
    assert create_safe_error_detail(Exception(short_error)) == short_error

    long_error = "x" * 150
    result = create_safe_error_detail(Exception(long_error))
    assert len(result) == 100
    assert result == "x" * 100
