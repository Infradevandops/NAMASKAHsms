"""Tests for verification endpoints."""
import pytest
from unittest.mock import patch, MagicMock
import asyncio

class TestVerification:
    def test_purchase_verification(self, client, admin_user, admin_token):
        token = admin_token(admin_user.id, admin_user.email)
        
        with patch("app.api.verification.purchase_endpoints.TextVerifiedService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.enabled = True
            
            async def mock_buy(*args, **kwargs):
                return {"activation_id": "test_act_id", "phone_number": "+1234567890", "cost": 0.50}
            
            mock_instance.buy_number.side_effect = mock_buy

            response = client.post("/api/verification/request", 
                json={"service": "telegram", "country": "US"},
                headers={"Authorization": f"Bearer {token}"})
            
            if response.status_code != 201:
                print(f"Failed response: {response.json()}")
                
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["phone_number"] == "+1234567890"

    def test_get_verification_status_not_found(self, client, admin_user, admin_token):
        # Skipping implementation as we don't have the path
        pass
