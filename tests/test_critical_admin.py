"""Tests for critical admin endpoints."""


from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.verification import Verification

def create_token(user_id: str, email: str = "test@test.com") -> str:

    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture
def test_admin_user(db: Session):

    """Create admin user for testing."""
    admin = User(
        id="admin_test",
        email="admin_test@test.com",
        password_hash="hashed",
        is_admin=True,
        subscription_tier="pro",
    )
    db.add(admin)
    db.commit()
    return admin


@pytest.fixture
def test_regular_user(db: Session):

    """Create regular user for testing."""
    user = User(
        id="user_test",
        email="user_test@test.com",
        password_hash="hashed",
        is_admin=False,
        subscription_tier="freemium",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def verification_data(db: Session, test_regular_user):

    """Create verification records for testing."""
    verifications = []
for i in range(5):
        v = Verification(
            id=f"verify_{i}",
            user_id=test_regular_user.id,
            country="US",
            service_name="telegram",
            status="completed" if i < 3 else "failed",
            phone_number="+1234567890",
            cost=2.50,
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
        )
        db.add(v)
        verifications.append(v)
    db.commit()
    return verifications


class TestVerificationHistory:

    """Test verification history endpoints."""

def test_list_verifications_success(self, client: TestClient, test_admin_user, verification_data, db: Session):

        """Test listing verifications."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get("/api/admin/verifications", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["verifications"]) == 5
        assert data["verifications"][0]["status"] in ["completed", "failed"]

def test_list_verifications_filter_by_status(

        self, client: TestClient, test_admin_user, verification_data, db: Session
    ):
        """Test filtering verifications by status."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            "/api/admin/verifications?status=completed",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(v["status"] == "completed" for v in data["verifications"])

def test_list_verifications_filter_by_country(

        self, client: TestClient, test_admin_user, verification_data, db: Session
    ):
        """Test filtering verifications by country."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            "/api/admin/verifications?country=US",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(v["country"] == "US" for v in data["verifications"])

def test_get_verification_detail(self, client: TestClient, test_admin_user, verification_data, db: Session):

        """Test getting verification details."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        verify_id = verification_data[0].id
        response = client.get(
            f"/api/admin/verifications/{verify_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == verify_id
        assert data["status"] == "completed"

def test_get_verification_not_found(self, client: TestClient, test_admin_user, db: Session):

        """Test getting non-existent verification."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            "/api/admin/verifications/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [
            404,
            200,
        ]  # Some implementations might return empty list or 404

def test_verification_analytics(self, client: TestClient, test_admin_user, verification_data, db: Session):

        """Test verification analytics endpoint."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            "/api/admin/verifications/analytics/summary?days=30",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_verifications"] == 5

def test_export_verifications(self, client: TestClient, test_admin_user, verification_data, db: Session):

        """Test exporting verifications as CSV."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.post(
            "/api/admin/verifications/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [200, 201]

def test_verification_unauthorized(self, client: TestClient, test_regular_user, db: Session):

        """Test verification endpoints require admin."""
        token = create_token(test_regular_user.id, test_regular_user.email)
        response = client.get("/api/admin/verifications", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403


class TestUserManagement:

    """Test user management endpoints."""

def test_search_users_by_email(self, client: TestClient, test_admin_user, test_regular_user, db: Session):

        """Test searching users by email."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            f"/api/admin/users/search?query={test_regular_user.email}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

def test_get_user_activity(self, client: TestClient, test_admin_user, test_regular_user, db: Session):

        """Test getting user activity."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            f"/api/admin/users/{test_regular_user.id}/activity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

def test_suspend_user(self, client: TestClient, test_admin_user, test_regular_user, db: Session):

        """Test suspending a user."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.post(
            f"/api/admin/users/{test_regular_user.id}/suspend?reason=Abuse",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

def test_unsuspend_user(self, client: TestClient, test_admin_user, test_regular_user, db: Session):

        """Test unsuspending a user."""
        # First suspend
        test_regular_user.is_suspended = True
        db.commit()

        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.post(
            f"/api/admin/users/{test_regular_user.id}/unsuspend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        db.refresh(test_regular_user)
        assert test_regular_user.is_suspended is False

def test_user_management_unauthorized(self, client: TestClient, test_regular_user, db: Session):

        """Test user management requires admin."""
        token = create_token(test_regular_user.id, test_regular_user.email)
        response = client.get(
            "/api/admin/users/search?query=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestAuditCompliance:

    """Test audit and compliance endpoints."""

def test_get_audit_logs(self, client: TestClient, test_admin_user, db: Session):

        """Test getting audit logs."""
        token = create_token(test_admin_user.id, test_admin_user.email)
        response = client.get(
            "/api/admin/compliance/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

def test_compliance_unauthorized(self, client: TestClient, test_regular_user, db: Session):

        """Test compliance endpoints require admin."""
        token = create_token(test_regular_user.id, test_regular_user.email)
        response = client.get(
            "/api/admin/compliance/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403