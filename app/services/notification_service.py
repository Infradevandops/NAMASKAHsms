"""Notification service for managing in-app notifications."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification import Notification
from app.models.user import User

logger = get_logger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: Session):
        """Initialize notification service with database session."""
        self.db = db

    def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create a new notification.

        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data

        Returns:
            Created notification

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Create notification
        # Create notification
        # Note: Model does not support 'data' field currently
        notification = Notification(
            user_id=user_id, type=notification_type, title=title, message=message
        )

        self.db.add(notification)
        self.db.commit()

        logger.info(
            f"Notification created: User={user_id}, Type={notification_type}, "
            f"Title={title}"
        )

        return notification

    def get_notifications(
        self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20
    ) -> Dict[str, Any]:
        """Get notifications for user.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Dictionary with notifications and metadata

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        # Filter unread if requested
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        # Get total count
        total = query.count()

        # Get notifications
        notifications = (
            query.order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(min(limit, 100))
            .all()
        )

        logger.info(
            f"Retrieved {len(notifications)} notifications for user {user_id} "
            f"(total: {total}, unread_only: {unread_only})"
        )

        return {
            "user_id": user_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "notifications": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ],
        }

    def get_notification(self, notification_id: str, user_id: str) -> Notification:
        """Get a specific notification.

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Notification

        Raises:
            ValueError: If notification not found
        """
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            raise ValueError(f"Notification {notification_id} not found")

        logger.info(f"Retrieved notification: {notification_id}")

        return notification

    def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        """Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            Updated notification

        Raises:
            ValueError: If notification not found
        """
        notification = self.get_notification(notification_id, user_id)

        notification.is_read = True
        # notification.read_at = datetime.now(timezone.utc) # Model missing read_at

        self.db.commit()

        logger.info(f"Notification marked as read: {notification_id}")

        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Update all unread notifications
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({Notification.is_read: True})
        )

        self.db.commit()

        logger.info(f"Marked {count} notifications as read for user {user_id}")

        return count

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            True if deleted, False otherwise

        Raises:
            ValueError: If notification not found
        """
        notification = self.get_notification(notification_id, user_id)

        self.db.delete(notification)
        self.db.commit()

        logger.info(f"Notification deleted: {notification_id}")

        return True

    def delete_all_notifications(self, user_id: str) -> int:
        """Delete all notifications for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications deleted

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Delete all notifications
        count = (
            self.db.query(Notification).filter(Notification.user_id == user_id).delete()
        )

        self.db.commit()

        logger.info(f"Deleted {count} notifications for user {user_id}")

        return count

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

        logger.info(f"Unread notification count for user {user_id}: {count}")

        return count

    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Delete notifications older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of notifications deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        count = (
            self.db.query(Notification)
            .filter(Notification.created_at < cutoff_date)
            .delete(synchronize_session=False)
        )

        self.db.commit()

        logger.info(f"Deleted {count} notifications older than {days} days")

        return count

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: str = None,
        data: dict = None,
    ) -> bool:
        """Send an email notification."""
        logger.info(f"Sending email to {to_email}. Subject: {subject}")
        # In a real app, this would use an email backend (SES, SendGrid, SMTP)
        # For now, we simulate success
        return True
