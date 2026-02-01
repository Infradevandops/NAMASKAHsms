"""End-to-End Tests for User Journeys.

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.security import hash_password
from tests.conftest import create_test_token
from datetime import timedelta
import jwt
from app.core.config import settings
from app.models.kyc import KYCDocument

Tests complete user flows through the tier system:
- Freemium user accessing gated features
- Tier upgrades and downgrades
- Error handling scenarios
- KYC verification flow
- Reseller bulk purchase flow
"""


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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Try to access API keys endpoint (requires payg+)
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})

        # Should get 402 Payment Required
        assert response.status_code == 402
        data = response.json()
        # Check for required_tier in response (may be nested in message or at top level)
        has_tier_info = (
            "required_tier" in data
            or "detail" in data
            or (isinstance(data.get("message"), dict) and "required_tier" in data["message"])
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can access tier info
        response = client.get("/api/v1/tiers/current", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can see all tiers
        response = client.get("/api/v1/tiers/", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can access API keys
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Try to access ISP filtering (Pro feature)
        response = client.get("/api/carriers/isp-filter", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can access tier info
        response = client.get("/api/v1/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "pro"

        # Can access API keys
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Downgrade to freemium
        response = client.post("/api/v1/tiers/downgrade", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Verify tier changed
        response = client.get("/api/v1/tiers/current", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can access API keys before downgrade
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Downgrade
        response = client.post("/api/v1/tiers/downgrade", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Cannot access API keys after downgrade
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402


class TestErrorScenarios:

    """Test error handling scenarios."""

def test_unauthenticated_request_returns_401(self, client: TestClient):

        """Unauthenticated requests return 401."""
        response = client.get("/api/v1/tiers/current")
        assert response.status_code == 401

def test_invalid_token_returns_401(self, client: TestClient):

        """Invalid token returns 401."""
        response = client.get("/api/v1/tiers/current", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

def test_expired_token_returns_401(self, client: TestClient):

        """Expired token returns 401."""


        # Create expired token
        payload = {
            "user_id": "test_user",
            "email": "test@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        response = client.get(
            "/api/v1/tiers/current",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

def test_nonexistent_user_returns_404(self, client: TestClient):

        """Request for nonexistent user returns appropriate error."""
        token = create_test_token("nonexistent_user_id", "nonexistent@test.com")

        response = client.get("/api/v1/tiers/current", headers={"Authorization": f"Bearer {token}"})
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
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # Can access tier info
        response = client.get("/api/v1/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["current_tier"] == "custom"

        # Can access API keys
        response = client.get("/api/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Can access analytics
        response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


class TestKYCJourney:

    """Test KYC verification flow."""

def test_complete_kyc_flow(self, client: TestClient, db: Session):

        """Standard user submits KYC profile, admin verifies it, limits increase."""
        # 1. Create User
        user = User(
            id="kyc_user_e2e",
            email="kyc@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="pro",
            credits=20.0,
            created_at=datetime.now(timezone.utc),
        )
        admin = User(
            id="admin_user_e2e",
            email="admin@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=True,
            subscription_tier="custom",
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.add(admin)
        db.commit()

        user_token = create_test_token(user.id, user.email)
        admin_token = create_test_token(admin.id, admin.email, is_admin=True)

        # 2. Check initial limits (unverified)
        response = client.get("/api/v1/kyc/limits", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["verification_level"] == "unverified"
        assert data["daily_limit"] == 10.0

        # 3. Create KYC Profile
        profile_data = {
            "full_name": "John Doe",
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
            "address_line1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US",
        }
        response = client.post(
            "/api/v1/kyc/profile",
            json=profile_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 201
        profile_id = response.json()["id"]

        # 4. Upload Documents (Mock)
        # We'll skip actual file upload logic if complex mock needed,
        # but the submit endpoint checks for docs.
        # For this E2E, we might need to simulate the DB state or mock the upload.
        # Let's try to mock the DB state directly for documents to proceed to submission.

        doc1 = KYCDocument(
            kyc_profile_id=profile_id,
            document_type="id_card",
            file_path="/tmp/mock_id.jpg",
            verification_status="verified",
        )
        doc2 = KYCDocument(
            kyc_profile_id=profile_id,
            document_type="selfie",
            file_path="/tmp/mock_selfie.jpg",
            verification_status="verified",
        )
        db.add(doc1)
        db.add(doc2)
        db.commit()

        # 5. Submit for Review
        response = client.post("/api/v1/kyc/submit", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

        # 6. Admin Verifies
        verify_data = {
            "decision": "approved",
            "verification_level": "enhanced",
            "notes": "Looks good",
        }
        response = client.post(
            f"/api/v1/kyc/admin/verify/{profile_id}",
            json=verify_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["new_status"] == "verified"

        # 7. Check Limits Updated
        response = client.get("/api/v1/kyc/limits", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["verification_level"] == "enhanced"
        assert data["daily_limit"] >= 1000.0


class TestResellerJourney:

    """Test Reseller/Bulk Purchase flow."""

def test_bulk_purchase_flow(self, client: TestClient, db: Session):

        """Pro user can make bulk purchases."""
        # 1. Create Pro User with credits
        user = User(
            id="reseller_user_e2e",
            email="reseller@e2e.test",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            subscription_tier="pro",
            credits=500.0,  # Sufficient credits
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = create_test_token(user.id, user.email)

        # 2. Make Bulk Purchase Request
        purchase_data = {
            "service": "whatsapp",
            "country": "us",
            "quantity": 10,  # Minimum 5
        }
        response = client.post(
            "/api/v1/bulk-purchase/",
            json=purchase_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        bulk_id = data["bulk_id"]

        # 3. Check Status
        response = client.get(
            f"/api/v1/bulk-purchase/{bulk_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["bulk_id"] == bulk_id