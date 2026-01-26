"""Tests for notification center endpoints."""

import pytest
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        phone_number="+1234567890",
        password_hash="hashed_password",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_notifications(db: Session, test_user: User):
    """Create test notifications."""
    notifications = [
        Notification(
            user_id=test_user.id,
            type="verification_initiated",
            title="Verification Started",
            message="Your verification has started",
            is_read=False,
        ),
        Notification(
            user_id=test_user.id,
            type="sms_received",
            title="SMS Received",
            message="Your SMS code has been received",
            is_read=False,
        ),
        Notification(
            user_id=test_user.id,
            type="verification_complete",
            title="Verification Complete",
            message="Your verification is complete",
            is_read=True,
        ),
        Notification(
            user_id=test_user.id,
            type="credit_deducted",
            title="Credit Deducted",
            message="Credit has been deducted from your account",
            is_read=True,
        ),
    ]
    db.add_all(notifications)
    db.commit()
    return notifications


class TestNotificationCenter:
    """Test notification center endpoints."""

    def test_get_notification_center(self, client, test_user, test_notifications, auth_headers):
        """Test getting notifications with pagination."""
        response = client.get(
            "/api/notifications/center?skip=0&limit=10",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["notifications"]) == 4
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_get_notification_center_with_category_filter(self, client, test_user, test_notifications, auth_headers):
        """Test filtering notifications by category."""
        response = client.get(
            "/api/notifications/center?category=verification_initiated",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["notifications"][0]["type"] == "verification_initiated"

    def test_get_notification_center_with_read_filter(self, client, test_user, test_notifications, auth_headers):
        """Test filtering notifications by read status."""
        response = client.get(
            "/api/notifications/center?is_read=false",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for notif in data["notifications"]:
            assert notif["is_read"] is False

    def test_get_notification_center_with_sorting(self, client, test_user, test_notifications, auth_headers):
        """Test sorting notifications."""
        response = client.get(
            "/api/notifications/center?sort_by=oldest",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 4
        # Verify oldest first
        assert data["notifications"][0]["created_at"] <= data["notifications"][-1]["created_at"]

    def test_get_notification_categories(self, client, test_user, test_notifications, auth_headers):
        """Test getting notification categories."""
        response = client.get(
            "/api/notifications/categories",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 4

        # Verify category structure
        for category in data["categories"]:
            assert "type" in category
            assert "total" in category
            assert "unread" in category

    def test_search_notifications(self, client, test_user, test_notifications, auth_headers):
        """Test searching notifications."""
        response = client.post(
            "/api/notifications/search?query=verification",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["query"] == "verification"

    def test_search_notifications_min_length(self, client, test_user, test_notifications, auth_headers):
        """Test search with minimum length validation."""
        response = client.post(
            "/api/notifications/search?query=a",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 422  # Validation error

    def test_bulk_mark_as_read(self, client, test_user, test_notifications, auth_headers):
        """Test marking multiple notifications as read."""
        unread_ids = [n.id for n in test_notifications if not n.is_read]

        response = client.post(
            f"/api/notifications/bulk-read?notification_ids={unread_ids[0]}&notification_ids={unread_ids[1]}",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 2

    def test_bulk_delete_notifications(self, client, test_user, test_notifications, auth_headers):
        """Test deleting multiple notifications."""
        ids_to_delete = [test_notifications[0].id, test_notifications[1].id]

        response = client.post(
            f"/api/notifications/bulk-delete?notification_ids={ids_to_delete[0]}&notification_ids={ids_to_delete[1]}",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 2

    def test_export_notifications_json(self, client, test_user, test_notifications, auth_headers):
        """Test exporting notifications as JSON."""
        response = client.get(
            "/api/notifications/export?format=json",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "data" in data
        assert len(data["data"]) == 4

    def test_export_notifications_csv(self, client, test_user, test_notifications, auth_headers):
        """Test exporting notifications as CSV."""
        response = client.get(
            "/api/notifications/export?format=csv",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
        assert "data" in data
        assert "id,type,title,message,is_read,created_at" in data["data"]

    def test_unauthorized_access(self, client):
        """Test that unauthorized users cannot access notifications."""
        response = client.get("/api/notifications/center")
        assert response.status_code == 401

    def test_user_isolation(self, client, test_user, test_notifications, auth_headers, db: Session):
        """Test that users can only see their own notifications."""
        # Create another user
        other_user = User(
            id="other-user-456",
            email="other@example.com",
            phone_number="+9876543210",
            password_hash="hashed_password",
        )
        db.add(other_user)
        db.commit()

        # Get notifications as first user
        response = client.get(
            "/api/notifications/center",
            headers=auth_headers(test_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4

        # Get notifications as second user (should be empty)
        response = client.get(
            "/api/notifications/center",
            headers=auth_headers(other_user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
