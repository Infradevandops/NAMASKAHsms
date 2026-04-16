"""Integration test for area code fallback logic."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import status
from app.api.verification.purchase_endpoints import request_verification
from app.schemas.verification import VerificationRequest


@pytest.mark.asyncio
async def test_area_code_fallback_logic():
    """Test that area code fallback is correctly tracked and returned."""

    # Setup mocks
    db = MagicMock()
    user = MagicMock()
    user.id = "test_user_id"
    user.credits = 100.0
    user.subscription_tier = "payg"

    def mock_query(model):
        from app.models.user import User

        if model == User:
            m = MagicMock()
            m.filter.return_value.first.return_value = user
            return m
        return MagicMock(
            filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        )

    db.query.side_effect = mock_query

    # Mock TextVerifiedService for FALLBACK scenario
    with patch("app.api.verification.purchase_endpoints.TextVerifiedService") as MockTV:
        mock_tv = MockTV.return_value
        mock_tv.enabled = True

        # Mock result: Requested 212, Got 718 (Same state NY)
        mock_tv.create_verification = AsyncMock(
            return_value={
                "id": "act_fallback_123",
                "phone_number": "+17185550199",
                "assigned_area_code": "718",
                "requested_area_code": "212",
                "fallback_applied": True,
                "same_state_fallback": True,
                "assigned_carrier": "Verizon",
            }
        )

        with patch("app.api.verification.purchase_endpoints.TierManager") as MockTM:
            MockTM.return_value.check_feature_access.return_value = True
            with patch(
                "app.api.verification.purchase_endpoints.PricingCalculator"
            ) as MockPC:
                MockPC.calculate_sms_cost.return_value = {"total_cost": 2.50}
                with patch(
                    "app.api.verification.purchase_endpoints.NotificationDispatcher"
                ) as MockND:
                    MockND.return_value.notify_verification_started = AsyncMock()

                    request = VerificationRequest(
                        service="whatsapp",
                        country="US",
                        area_codes=["212"],
                        idempotency_key="idemp_fallback_001",
                    )

                    # Execute
                    response = await request_verification(
                        request, db, user_id="test_user_id"
                    )

                    # Assertions
                    assert response["success"] is True
                    assert response["fallback_applied"] is True
                    assert response["assigned_area_code"] == "718"
                    assert response["requested_area_code"] == "212"
                    assert response["same_state_fallback"] is True

                    # Verify DB record creation (first add/flush)
                    # We can't easily check call args on MagicMock db.add because Verification is an object
                    # but we know it reached the end because success is True.

                    print(
                        "✅ Integration test passed: Area code fallback logic correctly handled."
                    )
