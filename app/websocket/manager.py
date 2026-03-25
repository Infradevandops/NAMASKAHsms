"""WebSocket connection manager for real-time notifications."""

import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(
            f"✅ WebSocket connected: user={user_id}, "
            f"total_connections={len(self.active_connections[user_id])}"
        )

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
            logger.info(f"🔌 All connections closed for user {user_id}")
        else:
            logger.info(
                f"🔌 WebSocket disconnected: user={user_id}, "
                f"remaining={len(self.active_connections[user_id])}"
            )

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's connections."""
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return

        disconnected = set()

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
                logger.debug(f"📤 Sent message to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        user_count = len(self.active_connections)
        logger.info(f"📢 Broadcasting to {user_count} users")

        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for user."""
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_connected_users(self) -> int:
        """Get number of users with active connections."""
        return len(self.active_connections)

    def is_user_connected(self, user_id: str) -> bool:
        return bool(self.active_connections.get(user_id))

    async def broadcast_to_user(self, user_id: str, message: dict) -> bool:
        if not self.is_user_connected(user_id):
            return False
        await self.send_personal_message(message, user_id)
        return True

    def subscribe_user(self, user_id: str, channel: str) -> bool:
        if not hasattr(self, "_channels"):
            self._channels: Dict[str, Set[str]] = {}
        self._channels.setdefault(channel, set()).add(user_id)
        return True

    def unsubscribe_user(self, user_id: str, channel: str) -> bool:
        if hasattr(self, "_channels") and channel in self._channels:
            self._channels[channel].discard(user_id)
        return True

    async def broadcast_to_channel(self, channel: str, message: dict) -> int:
        if not hasattr(self, "_channels"):
            return 0
        sent = 0
        for user_id in self._channels.get(channel, set()):
            if await self.broadcast_to_user(user_id, message):
                sent += 1
        return sent

    def get_active_connections_count(self) -> int:
        return self.get_total_connections()

    def get_active_users(self) -> list:
        return list(self.active_connections.keys())


# Global instance
manager = ConnectionManager()
