"""Tests for billing endpoints."""
import pytest

class TestBilling:
    def test_get_pricing_services(self, client):
        response = client.get("/api/pricing/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "telegram" in data["services"]
    
    def test_get_balance(self, client, regular_user, user_token):
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/api/user/balance",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
        assert data["credits"] == 10.0  # From fixture
    
    def test_add_credits_admin(self, client, admin_user, admin_token):
        token = admin_token(admin_user.id, admin_user.email)
        initial_balance = admin_user.credits
        amount_to_add = 50.0
        
        response = client.post("/api/user/credits/add",
            params={"amount": amount_to_add, "description": "Test credit"},
            headers={"Authorization": f"Bearer {token}"})
            
        assert response.status_code == 200
        data = response.json()
        
        # credit_service.add_credits returns specific structure
        assert data["amount_added"] == amount_to_add
        assert data["new_balance"] == initial_balance + amount_to_add

    def test_add_credits_non_admin_fails(self, client, regular_user, user_token):
        token = user_token(regular_user.id, regular_user.email)
        response = client.post("/api/user/credits/add",
            params={"amount": 10.0},
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
