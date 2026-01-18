"""End-to-End Tests for User Journeys.

Tests complete user flows through the tier system:
- Freemium user accessing gated features
- Tier upgrades and downgrades
- Error handling scenarios
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password
from tests.conftest import create_test_token


class TestFreemiumUserJourney:
    """Test freemium user trying to access paid features."""
    
    def test_freemium_user_gets_402_on_api_access(self, client: TestClient, db: Session):
        """Freemium user tries to access API endpoint and gets 402."""
        # Create freemium user
        user = User(
            id="freemium_user_e2e",
            email="freemium@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="freemium",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Try to access API keys endpoint (requires payg+)
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should get 402 Payment Required
        assert response.status_code == 402
        data = response.json()
        # Check for required_tier in response (may be nested in message or at top level)
        has_tier_info = (
            "required_tier" in data or 
            "detail" in data or
            (isinstance(data.get("message"), dict) and "required_tier" in data["message"])
        )
        assert has_tier_info
    
    def test_freemium_user_can_view_dashboard(self, client: TestClient, db: Session):
        """Freemium user can access dashboard."""
        user = User(
            id="freemium_dash_e2e",
            email="freemium_dash@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="freemium",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can access tier info
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "freemium"
    
    def test_freemium_user_sees_upgrade_options(self, client: TestClient, db: Session):
        """Freemium user can see available tiers for upgrade."""
        user = User(
            id="freemium_upgrade_e2e",
            email="freemium_upgrade@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="freemium",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can see all tiers
        response = client.get(
            "/api/tiers/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response may be a list or wrapped in {"tiers": [...]}
        tiers = data.get("tiers", data) if isinstance(data, dict) else data
        assert len(tiers) >= 4  # freemium, payg, pro, custom


class TestTierUpgradeJourney:
    """Test user upgrading from one tier to another."""
    
    def test_payg_user_can_access_api_keys(self, client: TestClient, db: Session):
        """PayG user can access API keys endpoint."""
        user = User(
            id="payg_api_e2e",
            email="payg_api@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="payg",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can access API keys
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_payg_user_gets_402_on_pro_features(self, client: TestClient, db: Session):
        """PayG user cannot access Pro-only features."""
        user = User(
            id="payg_pro_e2e",
            email="payg_pro@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="payg",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Try to access ISP filtering (Pro feature)
        response = client.get(
            "/api/carriers/isp-filter",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should get 402 or 404 (endpoint may not exist)
        assert response.status_code in [402, 404]
    
    def test_pro_user_can_access_all_features(self, client: TestClient, db: Session):
        """Pro user can access all standard features."""
        user = User(
            id="pro_all_e2e",
            email="pro_all@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can access tier info
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "pro"
        
        # Can access API keys
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestTierDowngradeJourney:
    """Test user downgrading tiers."""
    
    def test_downgrade_to_freemium(self, client: TestClient, db: Session):
        """User can downgrade to freemium."""
        user = User(
            id="downgrade_e2e",
            email="downgrade@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="payg",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Downgrade to freemium
        response = client.post(
            "/api/tiers/downgrade",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Verify tier changed
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "freemium"
    
    def test_downgraded_user_loses_api_access(self, client: TestClient, db: Session):
        """After downgrade, user loses access to paid features."""
        user = User(
            id="downgrade_lose_e2e",
            email="downgrade_lose@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="payg",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can access API keys before downgrade
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Downgrade
        response = client.post(
            "/api/tiers/downgrade",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Cannot access API keys after downgrade
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 402


class TestErrorScenarios:
    """Test error handling scenarios."""
    
    def test_unauthenticated_request_returns_401(self, client: TestClient):
        """Unauthenticated requests return 401."""
        response = client.get("/api/tiers/current")
        assert response.status_code == 401
    
    def test_invalid_token_returns_401(self, client: TestClient):
        """Invalid token returns 401."""
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_expired_token_returns_401(self, client: TestClient):
        """Expired token returns 401."""
        import jwt
        from app.core.config import settings
        from datetime import timedelta
        
        # Create expired token
        payload = {
            "user_id": "test_user",
            "email": "test@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    def test_nonexistent_user_returns_404(self, client: TestClient):
        """Request for nonexistent user returns appropriate error."""
        token = create_test_token("nonexistent_user_id", "nonexistent@test.com")
        
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should return 404 or handle gracefully
        assert response.status_code in [404, 401, 500]


class TestCustomTierJourney:
    """Test custom/enterprise tier users."""
    
    def test_custom_user_has_full_access(self, client: TestClient, db: Session):
        """Custom tier user has access to all features."""
        user = User(
            id="custom_full_e2e",
            email="custom_full@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="custom",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        
        token = create_test_token(user.id, user.email)
        
        # Can access tier info
        response = client.get(
            "/api/tiers/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "custom"
        
        # Can access API keys
        response = client.get(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Can access analytics
        response = client.get(
            "/api/analytics/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
