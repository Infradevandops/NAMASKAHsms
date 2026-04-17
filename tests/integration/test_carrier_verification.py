"""Integration test for carrier verification and mismatch handling."""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to sys.path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi import HTTPException

from app.api.verification.purchase_endpoints import request_verification
from app.schemas.verification import VerificationRequest


@pytest.mark.asyncio
async def test_carrier_preference_accepted_as_best_effort():
    """Test that carrier preference is accepted even if TextVerified returns different carrier.

    FIXED: Carrier selection is now treated as a preference, not a guarantee.
    TextVerified returns generic types (Mobile, Landline) not specific carriers.
    Verification succeeds regardless of carrier mismatch.
    """

    # Mock dependencies
    db = MagicMock()
    user = MagicMock()
    user.id = "test_user_id"
    user.credits = 100.0
    user.subscription_tier = "pro"

    # Specific mock for User query
    def mock_query(model):
        from app.models.user import User

        if model == User:
            m = MagicMock()
            m.filter.return_value.first.return_value = user
            return m
        # For Verification(idempotency check), return None
        m = MagicMock()
        m.filter.return_value.first.return_value = None
        return m

    db.query.side_effect = mock_query

    # Mock TextVerifiedService
    with patch("app.api.verification.purchase_endpoints.TextVerifiedService") as MockTV:
        mock_tv = MockTV.return_value
        mock_tv.enabled = True
        mock_tv.api_key = "test_key"
        mock_tv.api_username = "test_user"

        # Mock successful create_verification with generic carrier response
        mock_tv.create_verification = AsyncMock(
            return_value={
                "id": "tv_id_123",
                "phone_number": "+14155550199",
                "assigned_carrier": "Mobile",  # TextVerified returns generic type
                "assigned_area_code": "415",
                "fallback_applied": False,
                "same_state_fallback": True,
            }
        )

        # Mock TierManager
        with patch("app.api.verification.purchase_endpoints.TierManager") as MockTM:
            MockTM.return_value.check_feature_access.return_value = True

            # Mock PricingCalculator
            with patch(
                "app.api.verification.purchase_endpoints.PricingCalculator"
            ) as MockPC:
                MockPC.calculate_sms_cost.return_value = {"total_cost": 2.75}

                # Request Verizon
                request = VerificationRequest(
                    service="telegram",
                    country="US",
                    carriers=["Verizon"],  # Requested Verizon
                    idempotency_key="550e8400-e29b-41d4-a716-446655440000",
                )

                # Execute
                result = await request_verification(request, db, user_id="test_user_id")

                # Verify success (no 409 error)
                assert result["success"] is True
                assert result["phone_number"] == "+14155550199"
                assert result["requested_carrier"] == "verizon"
                assert result["status"] == "pending"

                print(
                    "✅ Carrier preference test passed: Verification accepted with generic carrier response."
                )


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_carrier_preference_accepted_as_best_effort())
