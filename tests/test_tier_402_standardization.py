"""Tests for standardized 402 tier error responses."""

from datetime import datetime

import pytest
from fastapi import HTTPException

from app.core.tier_helpers import raise_tier_error
from app.schemas.tier_response import TierAccessDenied


def test_tier_access_denied_schema():
    """Test TierAccessDenied schema structure."""
    response = TierAccessDenied(
        message="Test message",
        current_tier="Freemium",
        required_tier="Pro",
        timestamp=datetime.utcnow(),
    )

    assert response.message == "Test message"
    assert response.current_tier == "Freemium"
    assert response.required_tier == "Pro"
    assert response.upgrade_url == "/billing/upgrade"
    assert isinstance(response.timestamp, datetime)


def test_raise_tier_error_structure():
    """Test raise_tier_error raises HTTPException with correct structure."""
    with pytest.raises(HTTPException) as exc_info:
        raise_tier_error("Freemium", "Pro", "user123")

    assert exc_info.value.status_code == 402
    detail = exc_info.value.detail
    assert detail["message"] == "This feature requires Pro tier or higher"
    assert detail["current_tier"] == "Freemium"
    assert detail["required_tier"] == "Pro"
    assert detail["upgrade_url"] == "/billing/upgrade"
    assert "timestamp" in detail


def test_raise_tier_error_without_user_id():
    """Test raise_tier_error works without user_id."""
    with pytest.raises(HTTPException) as exc_info:
        raise_tier_error("Pay-As-You-Go", "Custom")

    assert exc_info.value.status_code == 402
    assert exc_info.value.detail["current_tier"] == "Pay-As-You-Go"
    assert exc_info.value.detail["required_tier"] == "Custom"


def test_raise_tier_error_message_format():
    """Test error message format is consistent."""
    with pytest.raises(HTTPException) as exc_info:
        raise_tier_error("Freemium", "Pro")

    message = exc_info.value.detail["message"]
    assert "Pro" in message
    assert "tier" in message.lower()
    assert "requires" in message.lower()
