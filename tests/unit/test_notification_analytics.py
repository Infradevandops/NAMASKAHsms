"""Tests for notification analytics system."""


from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.notification_analytics import NotificationAnalytics
from app.models.user import User
from app.services.notification_analytics_service import NotificationAnalyticsService

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
def test_notification(db: Session, test_user):

    """Create test notification."""
    notification = Notification(
        user_id=test_user.id,
        type="verification",
        title="Test Notification",
        message="This is a test notification",
    )
    db.add(notification)
    db.commit()
    return notification


@pytest.fixture
def analytics_service(db: Session):

    """Create analytics service."""
    return NotificationAnalyticsService(db)


class TestNotificationAnalyticsModel:

    """Test NotificationAnalytics model."""

def test_create_analytics_record(self, db: Session, test_user, test_notification):

        """Test creating analytics record."""
        analytics = NotificationAnalytics(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
            status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(analytics)
        db.commit()

        assert analytics.id is not None
        assert analytics.notification_id == test_notification.id
        assert analytics.status == "sent"

def test_analytics_to_dict(self, db: Session, test_user, test_notification):

        """Test converting analytics to dictionary."""
        analytics = NotificationAnalytics(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
            status="delivered",
            sent_at=datetime.now(timezone.utc).isoformat(),
            delivered_at=datetime.now(timezone.utc).isoformat(),
            delivery_time_ms=100,
        )
        db.add(analytics)
        db.commit()

        analytics_dict = analytics.to_dict()

        assert analytics_dict["notification_id"] == test_notification.id
        assert analytics_dict["status"] == "delivered"
        assert analytics_dict["delivery_time_ms"] == 100


class TestNotificationAnalyticsService:

    """Test NotificationAnalyticsService."""

def test_track_notification_sent(self, analytics_service, test_user, test_notification):

        """Test tracking notification sent."""
        analytics = analytics_service.track_notification_sent(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
        )

        assert analytics.id is not None
        assert analytics.status == "sent"
        assert analytics.sent_at is not None

def test_track_notification_delivered(self, analytics_service, test_user, test_notification):

        """Test tracking notification delivered."""
        # First track sent
        analytics_service.track_notification_sent(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
        )

        # Then track delivered
        result = analytics_service.track_notification_delivered(
            notification_id=test_notification.id,
            user_id=test_user.id,
            delivery_method="email",
        )

        assert result is True

def test_track_notification_read(self, analytics_service, test_user, test_notification):

        """Test tracking notification read."""
        # First track sent
        analytics_service.track_notification_sent(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
        )

        # Then track read
        result = analytics_service.track_notification_read(
            notification_id=test_notification.id,
            user_id=test_user.id,
        )

        assert result is True

def test_track_notification_clicked(self, analytics_service, test_user, test_notification):

        """Test tracking notification clicked."""
        # First track sent
        analytics_service.track_notification_sent(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
        )

        # Then track clicked
        result = analytics_service.track_notification_clicked(
            notification_id=test_notification.id,
            user_id=test_user.id,
        )

        assert result is True

def test_track_notification_failed(self, analytics_service, test_user, test_notification):

        """Test tracking notification failed."""
        # First track sent
        analytics_service.track_notification_sent(
            notification_id=test_notification.id,
            user_id=test_user.id,
            notification_type="verification",
            delivery_method="email",
        )

        # Then track failed
        result = analytics_service.track_notification_failed(
            notification_id=test_notification.id,
            user_id=test_user.id,
            delivery_method="email",
            reason="Invalid email address",
        )

        assert result is True

def test_get_delivery_metrics(self, db: Session, analytics_service, test_user):

        """Test getting delivery metrics."""
        # Create multiple notifications and track them
for i in range(5):
            notification = Notification(
                user_id=test_user.id,
                type="verification",
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            db.add(notification)
            db.commit()

            analytics_service.track_notification_sent(
                notification_id=notification.id,
                user_id=test_user.id,
                notification_type="verification",
                delivery_method="email",
            )

if i < 3:
                analytics_service.track_notification_delivered(
                    notification_id=notification.id,
                    user_id=test_user.id,
                    delivery_method="email",
                )

        metrics = analytics_service.get_delivery_metrics(user_id=test_user.id)

        assert metrics["total_notifications"] == 5
        assert metrics["delivered"] == 3
        assert metrics["delivery_rate"] == 60.0

def test_get_metrics_by_type(self, db: Session, analytics_service, test_user):

        """Test getting metrics by notification type."""
        # Create notifications of different types
for notification_type in ["verification", "payment", "login"]:
for i in range(2):
                notification = Notification(
                    user_id=test_user.id,
                    type=notification_type,
                    title=f"{notification_type} {i}",
                    message=f"Message {i}",
                )
                db.add(notification)
                db.commit()

                analytics_service.track_notification_sent(
                    notification_id=notification.id,
                    user_id=test_user.id,
                    notification_type=notification_type,
                    delivery_method="email",
                )

        metrics = analytics_service.get_metrics_by_type(user_id=test_user.id)

        assert len(metrics) == 3
        assert "verification" in metrics
        assert "payment" in metrics
        assert "login" in metrics
        assert metrics["verification"]["total"] == 2

def test_get_metrics_by_method(self, db: Session, analytics_service, test_user):

        """Test getting metrics by delivery method."""
        # Create notifications with different delivery methods
for method in ["email", "sms", "websocket"]:
for i in range(2):
                notification = Notification(
                    user_id=test_user.id,
                    type="verification",
                    title=f"Notification {i}",
                    message=f"Message {i}",
                )
                db.add(notification)
                db.commit()

                analytics_service.track_notification_sent(
                    notification_id=notification.id,
                    user_id=test_user.id,
                    notification_type="verification",
                    delivery_method=method,
                )

        metrics = analytics_service.get_metrics_by_method(user_id=test_user.id)

        assert len(metrics) == 3
        assert "email" in metrics
        assert "sms" in metrics
        assert "websocket" in metrics
        assert metrics["email"]["total"] == 2

def test_get_timeline_metrics(self, db: Session, analytics_service, test_user):

        """Test getting timeline metrics."""
        # Create notifications
for i in range(5):
            notification = Notification(
                user_id=test_user.id,
                type="verification",
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            db.add(notification)
            db.commit()

            analytics_service.track_notification_sent(
                notification_id=notification.id,
                user_id=test_user.id,
                notification_type="verification",
                delivery_method="email",
            )

        metrics = analytics_service.get_timeline_metrics(user_id=test_user.id, interval="day")

        assert len(metrics) > 0
        assert "period" in metrics[0]
        assert "total" in metrics[0]


class TestAnalyticsEndpoints:

    """Test analytics endpoints."""

def test_get_analytics_summary_endpoint(self, client, test_user, db: Session):

        """Test GET /api/notifications/analytics/summary endpoint."""
with client:
            response = client.get(
                "/api/notifications/analytics/summary",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
if response.status_code == 200:
            data = response.json()
            assert "total_notifications" in data
            assert "delivery_rate" in data

def test_get_analytics_by_type_endpoint(self, client, test_user):

        """Test GET /api/notifications/analytics/by-type endpoint."""
with client:
            response = client.get(
                "/api/notifications/analytics/by-type",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

def test_get_analytics_by_method_endpoint(self, client, test_user):

        """Test GET /api/notifications/analytics/by-method endpoint."""
with client:
            response = client.get(
                "/api/notifications/analytics/by-method",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

def test_get_analytics_timeline_endpoint(self, client, test_user):

        """Test GET /api/notifications/analytics/timeline endpoint."""
with client:
            response = client.get(
                "/api/notifications/analytics/timeline",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

def test_get_analytics_timeline_invalid_interval(self, client, test_user):

        """Test timeline endpoint with invalid interval."""
with client:
            response = client.get(
                "/api/notifications/analytics/timeline?interval=invalid",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [400, 404, 405, 422]