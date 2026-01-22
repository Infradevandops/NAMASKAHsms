"""Tests for verification pricing endpoint."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_pricing_requires_service():
    """Test that pricing endpoint requires service parameter."""
    from app.api.verification.pricing import get_verification_pricing

    with pytest.raises(HTTPException) as exc:
        await get_verification_pricing(service="", user_id="test_user", db=Mock())
    assert exc.value.status_code == 400
    assert "Service required" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_pricing_basic_calculation():
    """Test basic pricing calculation without premium features."""
    from app.api.verification.pricing import get_verification_pricing

    mock_db = Mock()
    mock_tier_manager = Mock()
    mock_tier_manager.get_user_tier.return_value = "freemium"
    mock_tier_manager.check_feature_access.return_value = True

    mock_integration = AsyncMock()
    mock_integration.get_pricing.return_value = {"cost": 1.00}

    with patch(
        "app.api.verification.pricing.TierManager", return_value=mock_tier_manager
    ):
        with patch(
            "app.services.textverified_service.TextVerifiedService",
            return_value=mock_integration,
        ):
            result = await get_verification_pricing(
                service="whatsapp", country="US", user_id="test_user", db=mock_db
            )

    assert result["success"] is True
    assert result["service"] == "whatsapp"
    assert result["provider_cost"] == 1.00
    assert result["total_price"] == 1.10  # 10% margin
