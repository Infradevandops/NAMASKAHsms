"""Tests for critical admin endpoints."""
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.verification import Verification
from app.models.audit_log import AuditLog
from app.core.config import settings


def create_token(user_id: str, email: str = "test@test.com") -> str:
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture
def admin_user(db: Session):
    """Create admin user for testing."""
    admin = User(
        id="admin_test",
        email="admin@test.com",
        password_hash="hashed",
        is_admin=True,
        tier_id="custom"
    )
    db.add(admin)
    db.commit()
    return admin


@pytest.fixture
def regular_user(db: Session):
    """Create regular user for testing."""
    user = User(
        id="user_test",
        email="user@test.com",
        password_hash="hashed",
        is_admin=False,
        tier_id="starter",
        credits=100
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def verification_data(db: Session, regular_user):
    """Create verification records for testing."""
    verifications = []
    for i in range(5):
        v = Verification(
            id=f"verify_{i}",
            user_id=regular_user.id,
            country="US",
            service_name="telegram",
            status="completed" if i < 3 else "failed",
            phone_number="+1234567890",
            cost=2.50,
            created_at=datetime.now(timezone.utc) - timedelta(days=i)
        )
        db.add(v)
        verifications.append(v)
    db.commit()
    return verifications


class TestVerificationHistory:
    """Test verification history endpoints."""
    
    def test_list_verifications_success(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test listing verifications."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/verifications",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["verifications"]) == 5
        assert data["verifications"][0]["status"] in ["completed", "failed"]
    
    def test_list_verifications_filter_by_status(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test filtering verifications by status."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/verifications?status=completed",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(v["status"] == "completed" for v in data["verifications"])
    
    def test_list_verifications_filter_by_country(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test filtering verifications by country."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/verifications?country=US",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(v["country"] == "US" for v in data["verifications"])
    
    def test_get_verification_detail(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test getting verification details."""
        token = create_token(admin_user.id, admin_user.email)
        verify_id = verification_data[0].id
        response = client.get(
            f"/api/admin/verifications/{verify_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == verify_id
        assert data["status"] == "completed"
    
    def test_get_verification_not_found(self, client: TestClient, admin_user, db: Session):
        """Test getting non-existent verification."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/verifications/nonexistent",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
    
    def test_verification_analytics(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test verification analytics endpoint."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/verifications/analytics/summary?days=30",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_verifications"] == 5
        assert data["completed"] == 3
        assert data["failed"] == 2
        assert data["success_rate"] == 60.0
    
    def test_export_verifications(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test exporting verifications as CSV."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            "/api/admin/verifications/export",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 5
        assert "csv_data" in data
        assert "ID,User ID,Country" in data["csv_data"]
    
    def test_export_verifications_filtered(self, client: TestClient, admin_user, verification_data, db: Session):
        """Test exporting filtered verifications."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            "/api/admin/verifications/export?status=completed",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
    
    def test_verification_unauthorized(self, client: TestClient, regular_user, db: Session):
        """Test verification endpoints require admin."""
        token = create_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/admin/verifications",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints."""
    
    def test_search_users_by_email(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test searching users by email."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/users/search?query=user@test",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(u["email"] == "user@test.com" for u in data["users"])
    
    def test_search_users_by_id(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test searching users by ID."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/users/search?query=user_test",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert any(u["id"] == "user_test" for u in data["users"])
    
    def test_search_users_pagination(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test search pagination."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/users/search?query=test&limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    def test_get_user_activity(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test getting user activity."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            f"/api/admin/users/{regular_user.id}/activity",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == regular_user.id
        assert data["email"] == "user@test.com"
        assert "recent_verifications" in data
    
    def test_suspend_user(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test suspending a user."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/users/{regular_user.id}/suspend?reason=Abuse",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify user is suspended
        db.refresh(regular_user)
        assert regular_user.is_suspended is True
    
    def test_suspend_self_fails(self, client: TestClient, admin_user, db: Session):
        """Test cannot suspend yourself."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/users/{admin_user.id}/suspend?reason=Test",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
    
    def test_unsuspend_user(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test unsuspending a user."""
        # First suspend
        regular_user.is_suspended = True
        db.commit()
        
        # Then unsuspend
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/users/{regular_user.id}/unsuspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        db.refresh(regular_user)
        assert regular_user.is_suspended is False
    
    def test_ban_user(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test banning a user."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/users/{regular_user.id}/ban?reason=Fraud",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        db.refresh(regular_user)
        assert regular_user.is_banned is True
    
    def test_unban_user(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test unbanning a user."""
        # First ban
        regular_user.is_banned = True
        db.commit()
        
        # Then unban
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/users/{regular_user.id}/unban",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        db.refresh(regular_user)
        assert regular_user.is_banned is False
    
    def test_user_management_unauthorized(self, client: TestClient, regular_user, db: Session):
        """Test user management requires admin."""
        token = create_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/admin/users/search?query=test",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestAuditCompliance:
    """Test audit and compliance endpoints."""
    
    def test_get_audit_logs(self, client: TestClient, admin_user, db: Session):
        """Test getting audit logs."""
        # Create audit log
        log = AuditLog(
            id="log_1",
            user_id=admin_user.id,
            action="tier_update",
            resource_type="user",
            resource_id="user_123",
            details={"message": "Updated tier to pro"},
            ip_address="127.0.0.1"
        )
        db.add(log)
        db.commit()
        
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/compliance/audit-logs",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    def test_get_audit_logs_filter_by_action(self, client: TestClient, admin_user, db: Session):
        """Test filtering audit logs by action."""
        log = AuditLog(
            id="log_2",
            user_id=admin_user.id,
            action="suspend",
            resource_type="user",
            resource_id="user_456",
            details={"message": "Suspended user"},
            ip_address="127.0.0.1"
        )
        db.add(log)
        db.commit()
        
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/compliance/audit-logs?action=suspend",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(log["action"] == "suspend" for log in data["logs"])
    
    def test_get_compliance_report(self, client: TestClient, admin_user, db: Session):
        """Test generating compliance report."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/compliance/reports?report_type=summary&days=30",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "summary"
        assert "summary" in data
        assert "actions_by_admin" in data
    
    def test_export_user_data_gdpr(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test exporting user data for GDPR."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/compliance/export?user_id={regular_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["id"] == regular_user.id
        assert "verifications" in data["data"]
        assert "api_keys" in data["data"]
    
    def test_delete_user_data_gdpr(self, client: TestClient, admin_user, regular_user, db: Session):
        """Test deleting user data for GDPR right to be forgotten."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.post(
            f"/api/admin/compliance/delete-user-data?user_id={regular_user.id}&reason=GDPR%20request",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        db.refresh(regular_user)
        assert regular_user.is_deleted is True
        assert regular_user.is_active is False
    
    def test_get_data_retention_policy(self, client: TestClient, admin_user, db: Session):
        """Test getting data retention policy."""
        token = create_token(admin_user.id, admin_user.email)
        response = client.get(
            "/api/admin/compliance/data-retention-policy",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "policy" in data
        assert "user_data" in data["policy"]
        assert "compliance_standards" in data
    
    def test_compliance_unauthorized(self, client: TestClient, regular_user, db: Session):
        """Test compliance endpoints require admin."""
        token = create_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/admin/compliance/audit-logs",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
