"""WebSocket connection manager for real-time notifications."""


from typing import Dict, List, Optional
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:

    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):

        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, set] = {}  # user_id -> set of channels

    async def connect(self, user_id: str, websocket: WebSocket) -> bool:
        """Connect a user's WebSocket.

        Args:
            user_id: User ID
            websocket: WebSocket connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
            self.user_subscriptions[user_id] = {"notifications"}  # Default subscription

            logger.info(f"User {user_id} connected via WebSocket (total: {len(self.active_connections)})")
        return True

        except Exception as e:
            logger.error(f"Failed to connect user {user_id}: {e}")
        return False

    async def disconnect(self, user_id: str) -> bool:
        """Disconnect a user's WebSocket.

        Args:
            user_id: User ID

        Returns:
            True if disconnection successful, False otherwise
        """
        try:
        if user_id in self.active_connections:
                del self.active_connections[user_id]

        if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]

            logger.info(f"User {user_id} disconnected (total: {len(self.active_connections)})")
        return True

        except Exception as e:
            logger.error(f"Failed to disconnect user {user_id}: {e}")
        return False

    async def broadcast_to_user(self, user_id: str, message: dict) -> bool:
        """Send message to specific user.

        Args:
            user_id: User ID
            message: Message dictionary

        Returns:
            True if message sent successfully, False otherwise
        """
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected, skipping broadcast")
        return False

        try:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
            logger.debug(f"Message sent to user {user_id}")
        return True

        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            await self.disconnect(user_id)
        return False

    async def broadcast_to_all(self, message: dict) -> int:
        """Send message to all connected users.

        Args:
            message: Message dictionary

        Returns:
            Number of users message was sent to
        """
        sent_count = 0

        for user_id in list(self.active_connections.keys()):
        try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message)
                sent_count += 1

        except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                await self.disconnect(user_id)

        logger.info(f"Broadcast message sent to {sent_count} users")
        return sent_count

    async def broadcast_to_channel(self, channel: str, message: dict) -> int:
        """Send message to all users subscribed to a channel.

        Args:
            channel: Channel name
            message: Message dictionary

        Returns:
            Number of users message was sent to
        """
        sent_count = 0

        for user_id, subscriptions in self.user_subscriptions.items():
        if channel in subscriptions and user_id in self.active_connections:
        try:
                    websocket = self.active_connections[user_id]
                    await websocket.send_json(message)
                    sent_count += 1

        except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    await self.disconnect(user_id)

        logger.info(f"Channel '{channel}' broadcast sent to {sent_count} users")
        return sent_count

    def subscribe_user(self, user_id: str, channel: str) -> bool:

        """Subscribe user to a channel.

        Args:
            user_id: User ID
            channel: Channel name

        Returns:
            True if subscription successful, False otherwise
        """
        try:
        if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()

            self.user_subscriptions[user_id].add(channel)
            logger.debug(f"User {user_id} subscribed to channel '{channel}'")
        return True

        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id} to channel {channel}: {e}")
        return False

    def unsubscribe_user(self, user_id: str, channel: str) -> bool:

        """Unsubscribe user from a channel.

        Args:
            user_id: User ID
            channel: Channel name

        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
        if user_id in self.user_subscriptions:
                self.user_subscriptions[user_id].discard(channel)
                logger.debug(f"User {user_id} unsubscribed from channel '{channel}'")
        return True

        return False

        except Exception as e:
            logger.error(f"Failed to unsubscribe user {user_id} from channel {channel}: {e}")
        return False

    def get_active_connections_count(self) -> int:

        """Get number of active connections.

        Returns:
            Number of active connections
        """
        return len(self.active_connections)

    def get_active_users(self) -> List[str]:

        """Get list of active user IDs.

        Returns:
            List of active user IDs
        """
        return list(self.active_connections.keys())

    def is_user_connected(self, user_id: str) -> bool:

        """Check if user is connected.

        Args:
            user_id: User ID

        Returns:
            True if user is connected, False otherwise
        """
        return user_id in self.active_connections

    def get_user_subscriptions(self, user_id: str) -> Optional[set]:

        """Get user's channel subscriptions.

        Args:
            user_id: User ID

        Returns:
            Set of channel names or None if user not found
        """
        return self.user_subscriptions.get(user_id)


# Global connection manager instance
        connection_manager = ConnectionManager()
