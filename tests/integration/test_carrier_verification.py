"""Integration test for carrier verification and mismatch handling."""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi import HTTPException
from app.api.verification.purchase_endpoints import request_verification
from app.schemas.verification import VerificationRequest

@pytest.mark.asyncio
async def test_carrier_mismatch_triggers_cancellation():
    """Test that a carrier mismatch triggers a cancel call and raises 409 Conflict."""
    
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
        
        # Mock successful create_verification but with WRONG carrier
        mock_tv.create_verification = AsyncMock(return_value={
            "id": "tv_id_123",
            "phone_number": "+14155550199",
            "assigned_carrier": "T-Mobile", # Assigned T-Mobile
            "assigned_area_code": "415",
            "fallback_applied": False,
            "same_state_fallback": True
        })
        
        mock_tv.cancel_verification = AsyncMock(return_value={"success": True})
        
        # Mock TierManager
        with patch("app.api.verification.purchase_endpoints.TierManager") as MockTM:
            MockTM.return_value.check_feature_access.return_value = True
            
            # Mock PricingCalculator
            with patch("app.api.verification.purchase_endpoints.PricingCalculator") as MockPC:
                MockPC.calculate_sms_cost.return_value = {"total_cost": 2.75}
                
                # Request Verizon
                request = VerificationRequest(
                    service="telegram",
                    country="US",
                    carriers=["Verizon"], # Requested Verizon
                    idempotency_key="550e8400-e29b-41d4-a716-446655440000"
                )
                
                # Execute
                try:
                    result = await request_verification(request, db, user_id="test_user_id")
                    print(f"RESULT SUCCESS: {result}")
                    assert False, f"Should have raised HTTPException 409, but got success: {result}"
                except HTTPException as e:
                    print(f"Caught expected exception: {e.status_code} - {e.detail}")
                    assert e.status_code == 409
                    assert "Requested carrier" in str(e.detail)
                except Exception as ex:
                    print(f"Caught UNEXPECTED exception: {type(ex)} - {ex}")
                    raise
                
                # Verify cancel was called
                mock_tv.cancel_verification.assert_called_with("tv_id_123")
                print("✅ Carrier mismatch test passed: Verification cancelled correctly.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_carrier_mismatch_triggers_cancellation())
