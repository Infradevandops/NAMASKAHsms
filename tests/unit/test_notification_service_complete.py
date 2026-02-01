

from app.models.notification import Notification
from app.services.notification_service import NotificationService

class TestNotificationServiceComplete:

    """Comprehensive tests for NotificationService."""

def test_create_notification(self, db_session, regular_user):

        """Test creating a notification."""
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=regular_user.id,
            notification_type="info",
            title="Welcome",
            message="Welcome to Namaskah",
        )

        assert notif.id is not None
        assert notif.user_id == regular_user.id
        assert notif.is_read is False

def test_get_notifications(self, db_session, regular_user):

        """Test retrieving notifications."""
        service = NotificationService(db_session)

        # Create a few notifications
for i in range(5):
            service.create_notification(
                user_id=regular_user.id,
                notification_type="test",
                title=f"Test {i}",
                message=f"Message {i}",
            )

        result = service.get_notifications(regular_user.id)
        assert result["total"] == 5
        assert len(result["notifications"]) == 5

def test_mark_as_read(self, db_session, regular_user):

        """Test marking a notification as read."""
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=regular_user.id,
            notification_type="test",
            title="Read Me",
            message="Please read",
        )

        service.mark_as_read(notif.id, regular_user.id)

        db_session.refresh(notif)
        assert notif.is_read is True

def test_delete_notification(self, db_session, regular_user):

        """Test deleting a notification."""
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=regular_user.id,
            notification_type="test",
            title="Delete Me",
            message="Bye",
        )

        service.delete_notification(notif.id, regular_user.id)

        count = db_session.query(Notification).filter(Notification.id == notif.id).count()
        assert count == 0

def test_get_unread_count(self, db_session, regular_user):

        """Test unread count calculation."""
        service = NotificationService(db_session)

        service.create_notification(regular_user.id, "type", "t1", "m1")
        service.create_notification(regular_user.id, "type", "t2", "m2")

        assert service.get_unread_count(regular_user.id) == 2

        # Mark one as read
        notifs = service.get_notifications(regular_user.id)["notifications"]
        service.mark_as_read(notifs[0]["id"], regular_user.id)

        assert service.get_unread_count(regular_user.id) == 1