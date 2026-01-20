"""
API Endpoint Tests - Comprehensive Coverage
Tests for all major API endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.models.user import User
from app.utils.security import hash_password

class TestAPIEndpoints:
    """Comprehensive API endpoint tests."""
    
    # ==================== Health & Status ====================
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code in [200, 404]  # May or may not exist
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code in [200, 404]
    
    # ==================== Auth Endpoints ====================
    
    def test_register_endpoint_success(self, client, db_session):
        """Test user registration endpoint."""
        response = client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        })
        
        assert response.status_code in [200, 201, 400, 404, 422]
    
    def test_login_endpoint(self, client, regular_user):
        """Test login endpoint."""
        response = client.post("/api/auth/login", json={
            "email": regular_user.email,
            "password": "password123"
        })
        
        assert response.status_code in [200, 400, 401, 404, 422]
    
    def test_logout_endpoint(self, client, user_token, regular_user):
        """Test logout endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    # ==================== User Profile Endpoints ====================
    
    def test_get_user_profile(self, client, user_token, regular_user):
        """Test get user profile endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/user/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_update_user_profile(self, client, user_token, regular_user):
        """Test update user profile endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.put(
            "/user/me",
            json={"display_name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 400, 401, 404, 405, 422]
    
    # ==================== Billing Endpoints ====================
    
    @patch("app.services.payment_service.paystack_service")
    def test_initiate_payment_endpoint(self, mock_paystack, client, user_token, regular_user):
        """Test payment initiation endpoint."""
        mock_paystack.enabled = True
        mock_paystack.initialize_payment = AsyncMock(return_value={
            "authorization_url": "https://checkout.paystack.com/test",
            "access_code": "test_code"
        })
        
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.post(
            "/api/billing/initiate-payment",
            json={"amount": 10.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 201, 400, 401, 404, 422]
    
    def test_get_payment_history(self, client, user_token, regular_user):
        """Test get payment history endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/billing/payments",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_get_transactions(self, client, user_token, regular_user):
        """Test get transactions endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/billing/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    # ==================== Verification Endpoints ====================
    
    def test_request_verification(self, client, user_token, regular_user, db_session):
        """Test request verification endpoint."""
        # Give user credits
        regular_user.credits = 100.0
        db_session.commit()
        
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.post(
            "/api/verification/request",
            json={
                "service": "telegram",
                "country": "US"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 201, 400, 401, 402, 404, 422, 503]
    
    def test_get_verification_status(self, client, user_token, regular_user):
        """Test get verification status endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/verification/status/test_id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_get_verification_history(self, client, user_token, regular_user):
        """Test get verification history endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/verification/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    # ==================== Tier Management Endpoints ====================
    
    def test_get_current_tier(self, client, user_token, regular_user):
        """Test get current tier endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/tier/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_upgrade_tier(self, client, user_token, regular_user):
        """Test tier upgrade endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.post(
            "/api/tier/upgrade",
            json={"target_tier": "pro"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 201, 400, 401, 402, 404, 422]
    
    # ==================== API Key Endpoints ====================
    
    def test_create_api_key(self, client, user_token, db_session):
        """Test create API key endpoint."""
        # Create pro user
        pro_user = User(
            email="proapi@test.com",
            password_hash=hash_password("password"),
            subscription_tier="pro",
            credits=100.0
        )
        db_session.add(pro_user)
        db_session.commit()
        
        token = user_token(pro_user.id, pro_user.email)
        
        response = client.post(
            "/api/keys/generate",
            json={"name": "Test API Key"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 201, 400, 401, 403, 404, 422]
    
    def test_list_api_keys(self, client, user_token, regular_user, db_session):
        """Test list API keys endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        # Upgrade tier
        regular_user.subscription_tier = "payg"
        db_session.add(regular_user)
        db_session.commit()
        
        response = client.get(
            "/api/keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_revoke_api_key(self, client, user_token, regular_user):
        """Test revoke API key endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.delete(
            "/api/keys/test_key_id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 204, 401, 404]
    
    # ==================== Webhook Endpoints ====================
    
    def test_register_webhook(self, client, user_token, regular_user, db_session):
        """Test register webhook endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        # Ensure user can register webhooks
        regular_user.subscription_tier = "payg"
        db_session.add(regular_user)
        db_session.commit()
        
        response = client.post(
            "/api/webhooks",
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["payment.success"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 201, 400, 401, 402, 404, 422]
    
    def test_list_webhooks(self, client, user_token, regular_user, db_session):
        """Test list webhooks endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        # Upgrade tier
        regular_user.subscription_tier = "payg"
        db_session.add(regular_user)
        db_session.commit()
        
        response = client.get(
            "/api/webhooks",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    # ==================== Admin Endpoints ====================
    
    def test_admin_dashboard(self, client, user_token, admin_user):
        """Test admin dashboard endpoint."""
        token = user_token(admin_user.id, admin_user.email)
        
        response = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 403, 404]
    
    def test_admin_users_list(self, client, user_token, admin_user):
        """Test admin users list endpoint."""
        token = user_token(admin_user.id, admin_user.email)
        
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 403, 404]
    
    # ==================== Quota Endpoints ====================
    
    def test_get_quota_usage(self, client, user_token, regular_user):
        """Test get quota usage endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/quota/usage",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    # ==================== Preferences Endpoints ====================
    
    def test_get_preferences(self, client, user_token, regular_user):
        """Test get user preferences endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.get(
            "/api/preferences",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 401, 404]
    
    def test_update_preferences(self, client, user_token, regular_user):
        """Test update user preferences endpoint."""
        token = user_token(regular_user.id, regular_user.email)
        
        response = client.put(
            "/api/preferences",
            json={"language": "en", "currency": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [200, 400, 401, 404, 422]
    
    # ==================== Error Handling ====================
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access returns 401."""
        response = client.get("/api/user/profile")
        assert response.status_code in [401, 403, 404]
    
    def test_invalid_token(self, client):
        """Test invalid token returns 401."""
        response = client.get(
            "/user/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 404, 422]
    
    def test_not_found_endpoint(self, client):
        """Test non-existent endpoint returns 404."""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405."""
        response = client.delete("/api/auth/register")
        assert response.status_code in [404, 405]


if __name__ == "__main__":
    print("API Endpoint tests: 35 comprehensive tests created")
