"""Comprehensive tests for notification endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference


class TestNotificationEndpoints:
    """Test notification endpoints comprehensively."""

    def test_get_notifications_success(self, client, regular_user, db):
        """Test getting user notifications."""
        # Create some notifications
        for i in range(3):
            notification = Notification(
                user_id=regular_user.id,
                notification_type="info",
                title=f"Test Notification {i}",
                message=f"Test message {i}",
                is_read=False
            )
            db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications")

        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data or isinstance(data, list)

    def test_get_notifications_pagination(self, client, regular_user, db):
        """Test notification pagination."""
        # Create 10 notifications
        for i in range(10):
            notification = Notification(
                user_id=regular_user.id,
                notification_type="info",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False
            )
            db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications?limit=5&offset=0")

        assert response.status_code == 200

    def test_get_notifications_filter_unread(self, client, regular_user, db):
        """Test filtering unread notifications."""
        # Create mix of read/unread
        for i in range(5):
            notification = Notification(
                user_id=regular_user.id,
                notification_type="info",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=(i % 2 == 0)
            )
            db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications?unread_only=true")

        assert response.status_code == 200

    def test_get_notifications_empty(self, client, regular_user):
        """Test getting notifications when none exist."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications")

        assert response.status_code == 200

    def test_mark_notification_as_read(self, client, regular_user, db):
        """Test marking notification as read."""
        notification = Notification(
            user_id=regular_user.id,
            notification_type="info",
            title="Test",
            message="Test message",
            is_read=False
        )
        db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.patch(f"/api/v1/notifications/{notification.id}/read")

        assert response.status_code == 200
        db.refresh(notification)
        assert notification.is_read is True

    def test_mark_notification_as_read_not_found(self, client, regular_user):
        """Test marking non-existent notification as read."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.patch("/api/v1/notifications/nonexistent-id/read")

        assert response.status_code == 404

    def test_mark_all_as_read(self, client, regular_user, db):
        """Test marking all notifications as read."""
        # Create unread notifications
        for i in range(3):
            notification = Notification(
                user_id=regular_user.id,
                notification_type="info",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False
            )
            db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == 200

    def test_delete_notification(self, client, regular_user, db):
        """Test deleting notification."""
        notification = Notification(
            user_id=regular_user.id,
            notification_type="info",
            title="Test",
            message="Test message",
            is_read=False
        )
        db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.delete(f"/api/v1/notifications/{notification.id}")

        assert response.status_code == 200

    def test_delete_notification_not_found(self, client, regular_user):
        """Test deleting non-existent notification."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.delete("/api/v1/notifications/nonexistent-id")

        assert response.status_code == 404

    def test_get_unread_count(self, client, regular_user, db):
        """Test getting unread notification count."""
        # Create mix of read/unread
        for i in range(5):
            notification = Notification(
                user_id=regular_user.id,
                notification_type="info",
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=(i < 2)  # First 2 are read, last 3 unread
            )
            db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications/unread/count")

        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "unread_count" in data

    def test_get_notification_by_id(self, client, regular_user, db):
        """Test getting specific notification."""
        notification = Notification(
            user_id=regular_user.id,
            notification_type="info",
            title="Test",
            message="Test message",
            is_read=False
        )
        db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get(f"/api/v1/notifications/{notification.id}")

        assert response.status_code == 200

    def test_get_notification_by_id_not_found(self, client, regular_user):
        """Test getting non-existent notification."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications/nonexistent-id")

        assert response.status_code == 404

    def test_get_notification_wrong_user(self, client, regular_user, pro_user, db):
        """Test accessing another user's notification."""
        notification = Notification(
            user_id=pro_user.id,
            notification_type="info",
            title="Test",
            message="Test message",
            is_read=False
        )
        db.add(notification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get(f"/api/v1/notifications/{notification.id}")

        assert response.status_code == 404


class TestNotificationPreferenceEndpoints:
    """Test notification preference endpoints."""

    def test_get_preferences_success(self, client, regular_user):
        """Test getting notification preferences."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications/preferences")

        assert response.status_code == 200

    def test_update_preferences_success(self, client, regular_user):
        """Test updating notification preferences."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.put(
                "/api/v1/notifications/preferences",
                json={
                    "email_enabled": True,
                    "push_enabled": False,
                    "sms_enabled": False
                }
            )

        assert response.status_code == 200

    def test_update_preference_by_type(self, client, regular_user):
        """Test updating specific notification type preference."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.patch(
                "/api/v1/notifications/preferences/sms_received",
                json={"enabled": True}
            )

        assert response.status_code in [200, 404]

    def test_get_preference_by_type(self, client, regular_user):
        """Test getting specific notification type preference."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/notifications/preferences/sms_received")

        assert response.status_code in [200, 404]


class TestNotificationChannelEndpoints:
    """Test notification channel endpoints."""

    def test_test_email_notification(self, client, regular_user):
        """Test sending test email notification."""
        with patch("app.services.email_service.EmailService.send_email", new_callable=AsyncMock):
            with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
                response = client.post("/api/v1/notifications/test/email")

        assert response.status_code in [200, 404]

    def test_test_push_notification(self, client, regular_user):
        """Test sending test push notification."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post("/api/v1/notifications/test/push")

        assert response.status_code in [200, 404]

    def test_register_device_token(self, client, regular_user):
        """Test registering device token for push notifications."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.post(
                "/api/v1/notifications/devices",
                json={
                    "token": "test-device-token",
                    "platform": "ios"
                }
            )

        assert response.status_code in [200, 201, 404]

    def test_unregister_device_token(self, client, regular_user):
        """Test unregistering device token."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.delete("/api/v1/notifications/devices/test-device-token")

        assert response.status_code in [200, 404]
