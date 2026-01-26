"""Event broadcaster for sending notifications via WebSocket."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification import Notification
from app.websocket.manager import connection_manager

logger = get_logger(__name__)


class EventBroadcaster:
    """Service for broadcasting events to connected users via WebSocket."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize event broadcaster.

        Args:
            db: Database session (optional)
        """
        self.db = db

    async def broadcast_notification(
        self,
        user_id: str,
        notification: Notification,
    ) -> bool:
        """Broadcast notification to user via WebSocket.

        Args:
            user_id: User ID
            notification: Notification object

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            message = {
                "type": "notification",
                "channel": "notifications",
                "id": notification.id,
                "notification_type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "link": notification.link,
                "icon": notification.icon,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            success = await connection_manager.broadcast_to_user(user_id, message)

            if success:
                logger.info(f"Notification broadcasted to user {user_id} via WebSocket")
            else:
                logger.debug(f"User {user_id} not connected, notification not broadcasted")

            return success

        except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")
            return False

    async def broadcast_activity(
        self,
        user_id: str,
        activity_type: str,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Broadcast activity event to user via WebSocket.

        Args:
            user_id: User ID
            activity_type: Type of activity
            title: Activity title
            description: Activity description
            metadata: Additional metadata

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            message = {
                "type": "activity",
                "channel": "activities",
                "activity_type": activity_type,
                "title": title,
                "description": description,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            success = await connection_manager.broadcast_to_user(user_id, message)

            if success:
                logger.info(f"Activity broadcasted to user {user_id} via WebSocket")
            else:
                logger.debug(f"User {user_id} not connected, activity not broadcasted")

            return success

        except Exception as e:
            logger.error(f"Failed to broadcast activity: {e}")
            return False

    async def broadcast_payment_event(
        self,
        user_id: str,
        event_type: str,
        amount: float,
        reference: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Broadcast payment event to user via WebSocket.

        Args:
            user_id: User ID
            event_type: Type of payment event (initiated, completed, failed, refunded)
            amount: Payment amount
            reference: Payment reference
            status: Payment status
            metadata: Additional metadata

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            message = {
                "type": "payment",
                "channel": "payments",
                "event_type": event_type,
                "amount": amount,
                "reference": reference,
                "status": status,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            success = await connection_manager.broadcast_to_user(user_id, message)

            if success:
                logger.info(f"Payment event broadcasted to user {user_id} via WebSocket")
            else:
                logger.debug(f"User {user_id} not connected, payment event not broadcasted")

            return success

        except Exception as e:
            logger.error(f"Failed to broadcast payment event: {e}")
            return False

    async def broadcast_verification_event(
        self,
        user_id: str,
        event_type: str,
        service_name: str,
        verification_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Broadcast verification event to user via WebSocket.

        Args:
            user_id: User ID
            event_type: Type of verification event (initiated, completed, failed)
            service_name: Name of service
            verification_id: Verification ID
            status: Verification status
            metadata: Additional metadata

        Returns:
            True if broadcast successful, False otherwise
        """
        try:
            message = {
                "type": "verification",
                "channel": "notifications",
                "event_type": event_type,
                "service_name": service_name,
                "verification_id": verification_id,
                "status": status,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            success = await connection_manager.broadcast_to_user(user_id, message)

            if success:
                logger.info(f"Verification event broadcasted to user {user_id} via WebSocket")
            else:
                logger.debug(f"User {user_id} not connected, verification event not broadcasted")

            return success

        except Exception as e:
            logger.error(f"Failed to broadcast verification event: {e}")
            return False

    async def broadcast_to_channel(
        self,
        channel: str,
        message_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Broadcast message to all users on a channel.

        Args:
            channel: Channel name
            message_type: Type of message
            title: Message title
            content: Message content
            metadata: Additional metadata

        Returns:
            Number of users message was sent to
        """
        try:
            message = {
                "type": message_type,
                "channel": channel,
                "title": title,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            recipients = await connection_manager.broadcast_to_channel(channel, message)

            logger.info(f"Channel broadcast sent to {recipients} users on channel {channel}")

            return recipients

        except Exception as e:
            logger.error(f"Failed to broadcast to channel: {e}")
            return 0

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics.

        Returns:
            Dictionary with connection stats
        """
        try:
            active_connections = connection_manager.get_active_connections_count()
            active_users = connection_manager.get_active_users()

            return {
                "active_connections": active_connections,
                "active_users": len(active_users),
                "user_ids": active_users,
            }

        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {
                "active_connections": 0,
                "active_users": 0,
                "user_ids": [],
            }


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()
