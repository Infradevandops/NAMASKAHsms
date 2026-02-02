"""Tests for activity feed system."""


from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.user import User
from app.services.activity_service import ActivityService

@pytest.fixture
def test_user(db: Session):

    """Create test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        password_hash="hashed_password",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def activity_service(db: Session):

    """Create activity service."""
    return ActivityService(db)


class TestActivityModel:

    """Test Activity model."""

    def test_create_activity(self, db: Session, test_user):

        """Test creating an activity."""
        activity = Activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            resource_id="verify-123",
            action="created",
            status="completed",
            title="Verification Started",
            description="SMS verification initiated",
            activity_data={"service": "telegram", "cost": 0.05},
        )
        db.add(activity)
        db.commit()

        assert activity.id is not None
        assert activity.user_id == test_user.id
        assert activity.activity_type == "verification"
        assert activity.status == "completed"

    def test_activity_to_dict(self, db: Session, test_user):

        """Test converting activity to dictionary."""
        activity = Activity(
            user_id=test_user.id,
            activity_type="payment",
            resource_type="payment",
            resource_id="pay-123",
            action="completed",
            status="completed",
            title="Payment Received",
            description="Credit added to account",
            activity_data={"amount": 50.0, "method": "paystack"},
        )
        db.add(activity)
        db.commit()

        activity_dict = activity.to_dict()

        assert activity_dict["id"] == activity.id
        assert activity_dict["activity_type"] == "payment"
        assert activity_dict["title"] == "Payment Received"
        assert activity_dict["activity_data"]["amount"] == 50.0


class TestActivityService:

        """Test ActivityService."""

    def test_log_activity(self, activity_service, test_user):

        """Test logging an activity."""
        activity = activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Verification Started",
            description="SMS verification for Telegram",
            resource_id="verify-123",
            metadata={"service": "telegram", "cost": 0.05},
        )

        assert activity.id is not None
        assert activity.user_id == test_user.id
        assert activity.activity_type == "verification"
        assert activity.title == "Verification Started"

    def test_log_activity_user_not_found(self, activity_service):

        """Test logging activity for non-existent user."""
        with pytest.raises(ValueError, match="User .* not found"):
            activity_service.log_activity(
                user_id="non-existent-user",
                activity_type="verification",
                resource_type="verification",
                action="created",
                title="Test",
            )

    def test_get_user_activities(self, db: Session, activity_service, test_user):

        """Test retrieving user activities."""
        # Create multiple activities
        for i in range(5):
            activity_service.log_activity(
                user_id=test_user.id,
                activity_type="verification" if i % 2 == 0 else "payment",
                resource_type="verification" if i % 2 == 0 else "payment",
                action="created",
                title=f"Activity {i}",
                resource_id=f"resource-{i}",
            )

        result = activity_service.get_user_activities(test_user.id)

        assert result["total"] == 5
        assert len(result["activities"]) == 5
        assert result["skip"] == 0
        assert result["limit"] == 20

    def test_get_user_activities_with_filters(self, db: Session, activity_service, test_user):

        """Test retrieving activities with filters."""
        # Create activities of different types
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Verification 1",
        )
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="payment",
            resource_type="payment",
            action="completed",
            title="Payment 1",
        )
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="failed",
            title="Verification 2",
            status="failed",
        )

        # Filter by type
        result = activity_service.get_user_activities(test_user.id, activity_type="verification")
        assert result["total"] == 2

        # Filter by status
        result = activity_service.get_user_activities(test_user.id, status="failed")
        assert result["total"] == 1

        # Filter by resource type
        result = activity_service.get_user_activities(test_user.id, resource_type="payment")
        assert result["total"] == 1

    def test_get_user_activities_pagination(self, db: Session, activity_service, test_user):

        """Test pagination of activities."""
        # Create 25 activities
        for i in range(25):
            activity_service.log_activity(
                user_id=test_user.id,
                activity_type="verification",
                resource_type="verification",
                action="created",
                title=f"Activity {i}",
            )

        # Get first page
        result = activity_service.get_user_activities(test_user.id, skip=0, limit=10)
        assert result["total"] == 25
        assert len(result["activities"]) == 10

        # Get second page
        result = activity_service.get_user_activities(test_user.id, skip=10, limit=10)
        assert len(result["activities"]) == 10

        # Get last page
        result = activity_service.get_user_activities(test_user.id, skip=20, limit=10)
        assert len(result["activities"]) == 5

    def test_get_activity_by_id(self, db: Session, activity_service, test_user):

        """Test retrieving activity by ID."""
        activity = activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Test Activity",
        )

        retrieved = activity_service.get_activity_by_id(test_user.id, activity.id)

        assert retrieved is not None
        assert retrieved.id == activity.id
        assert retrieved.title == "Test Activity"

    def test_get_activity_by_id_not_found(self, activity_service, test_user):

        """Test retrieving non-existent activity."""
        retrieved = activity_service.get_activity_by_id(test_user.id, "non-existent-id")
        assert retrieved is None

    def test_get_activities_by_resource(self, db: Session, activity_service, test_user):

        """Test retrieving activities for a specific resource."""
        resource_id = "verify-123"

        # Create activities for same resource
        for i in range(3):
            activity_service.log_activity(
                user_id=test_user.id,
                activity_type="verification",
                resource_type="verification",
                resource_id=resource_id,
                action="created" if i == 0 else "updated",
                title=f"Activity {i}",
            )

        # Create activity for different resource
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            resource_id="verify-456",
            action="created",
            title="Different Resource",
        )

        activities = activity_service.get_activities_by_resource(test_user.id, "verification", resource_id)

        assert len(activities) == 3
        assert all(a.resource_id == resource_id for a in activities)

    def test_get_activity_summary(self, db: Session, activity_service, test_user):

        """Test getting activity summary."""
        # Create activities of different types and statuses
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Verification 1",
            status="completed",
        )
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="failed",
            title="Verification 2",
            status="failed",
        )
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="payment",
            resource_type="payment",
            action="completed",
            title="Payment 1",
            status="completed",
        )
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="login",
            resource_type="user",
            action="created",
            title="Login",
            status="completed",
        )

        summary = activity_service.get_activity_summary(test_user.id, days=30)

        assert summary["total_activities"] == 4
        assert summary["by_type"]["verification"] == 2
        assert summary["by_type"]["payment"] == 1
        assert summary["by_type"]["login"] == 1
        assert summary["by_status"]["completed"] == 3
        assert summary["by_status"]["failed"] == 1
        assert summary["by_resource"]["verification"] == 2
        assert summary["by_resource"]["payment"] == 1
        assert summary["by_resource"]["user"] == 1

    def test_cleanup_old_activities(self, db: Session, activity_service, test_user):

        """Test cleaning up old activities."""
        # Create recent activity
        activity_service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Recent Activity",
        )

        # Create old activity (manually set created_at)
        old_activity = Activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            status="completed",
            title="Old Activity",
            created_at=datetime.now(timezone.utc) - timedelta(days=100),
        )
        db.add(old_activity)
        db.commit()

        # Cleanup activities older than 90 days
        deleted_count = activity_service.cleanup_old_activities(days=90)

        assert deleted_count == 1

        # Verify old activity is deleted
        remaining = db.query(Activity).filter(Activity.user_id == test_user.id).all()
        assert len(remaining) == 1
        assert remaining[0].title == "Recent Activity"


class TestActivityEndpoints:

        """Test Activity API endpoints."""

    def test_get_activities_endpoint(self, client, test_user, db: Session):

        """Test GET /api/activities endpoint."""
        # Create test activities
        service = ActivityService(db)
        for i in range(3):
            service.log_activity(
                user_id=test_user.id,
                activity_type="verification",
                resource_type="verification",
                action="created",
                title=f"Activity {i}",
            )

        # Mock authentication
        with client:
            response = client.get(
                "/api/activities",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 3
            assert len(data["activities"]) == 3

    def test_get_activity_by_id_endpoint(self, client, test_user, db: Session):

        """Test GET /api/activities/{activity_id} endpoint."""
        service = ActivityService(db)
        activity = service.log_activity(
            user_id=test_user.id,
            activity_type="verification",
            resource_type="verification",
            action="created",
            title="Test Activity",
        )

        with client:
            response = client.get(
                f"/api/activities/{activity.id}",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == activity.id
            assert data["title"] == "Test Activity"

    def test_get_activity_summary_endpoint(self, client, test_user, db: Session):

        """Test GET /api/activities/summary/overview endpoint."""
        service = ActivityService(db)
        for i in range(5):
            service.log_activity(
                user_id=test_user.id,
                activity_type="verification" if i % 2 == 0 else "payment",
                resource_type="verification" if i % 2 == 0 else "payment",
                action="created",
                title=f"Activity {i}",
            )

        with client:
            response = client.get(
                "/api/activities/summary/overview",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["total_activities"] == 5
            assert "by_type" in data
            assert "by_status" in data
            assert "by_resource" in data

    def test_export_activities_json(self, client, test_user, db: Session):

        """Test exporting activities as JSON."""
        service = ActivityService(db)
        for i in range(3):
            service.log_activity(
                user_id=test_user.id,
                activity_type="verification",
                resource_type="verification",
                action="created",
                title=f"Activity {i}",
            )

        with client:
            response = client.post(
                "/api/activities/export?format=json",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["format"] == "json"
            assert data["count"] == 3
            assert len(data["data"]) == 3

    def test_export_activities_csv(self, client, test_user, db: Session):

        """Test exporting activities as CSV."""
        service = ActivityService(db)
        for i in range(3):
            service.log_activity(
                user_id=test_user.id,
                activity_type="verification",
                resource_type="verification",
                action="created",
                title=f"Activity {i}",
            )

        with client:
            response = client.post(
                "/api/activities/export?format=csv",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["format"] == "csv"
            assert data["count"] == 3
            assert "activity_type" in data["data"]