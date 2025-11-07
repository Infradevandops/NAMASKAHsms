"""WebSocket endpoint for real-time verification updates."""
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, verification_id: str):
        """Connect client to verification updates."""
        await websocket.accept()

        if verification_id not in self.active_connections:
            self.active_connections[verification_id] = set()

        self.active_connections[verification_id].add(websocket)

    def disconnect(self, websocket: WebSocket, verification_id: str):
        """Disconnect client."""
        if verification_id in self.active_connections:
            self.active_connections[verification_id].discard(websocket)

            if not self.active_connections[verification_id]:
                del self.active_connections[verification_id]

    async def send_update(self, verification_id: str, message: dict):
        """Send update to all connected clients for a verification."""
        if verification_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[verification_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except (ValueError, KeyError, TypeError, ConnectionError):
                    disconnected.add(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.active_connections[verification_id].discard(connection)


manager = ConnectionManager()


@router.websocket("/ws/verification/{verification_id}")
async def websocket_endpoint(websocket: WebSocket, verification_id: str):
    """WebSocket endpoint for verification updates."""
    await manager.connect(websocket, verification_id)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket, verification_id)
