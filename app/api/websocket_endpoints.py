"""WebSocket endpoints for real-time notifications."""

import json
from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.logging import get_logger
from app.websocket.manager import manager

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])
settings = get_settings()

_AUTH_TIMEOUT_SECONDS = 10


async def _authenticate_from_message(websocket: WebSocket) -> str:
    """
    Receive the first WebSocket message and extract the JWT token from it.
    Expects: {"type": "auth", "token": "<jwt>"}
    Raises ValueError on failure.
    """
    try:
        raw = await websocket.receive_text()
        msg = json.loads(raw)
    except Exception:
        raise ValueError("Expected JSON auth message as first frame")

    if msg.get("type") != "auth":
        raise ValueError("First message must be type='auth'")

    token = msg.get("token", "")
    if not token:
        raise ValueError("Missing token in auth message")

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise ValueError("No user_id in token")

    return user_id


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications.

    Auth flow (token is NOT passed in the URL to avoid log exposure):
        1. Client connects: ws://host/ws/notifications
        2. Client sends first message: {"type": "auth", "token": "<jwt>"}
        3. Server replies {"type": "connected"} on success, or closes with 1008.
    """
    await websocket.accept()
    user_id = None

    try:
        user_id = await _authenticate_from_message(websocket)
        logger.info(f"🔐 WebSocket auth successful: {user_id}")
    except Exception as e:
        logger.warning(f"❌ WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Register connection WITHOUT calling accept() again — already accepted above
    manager.register(websocket, user_id)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "message": "WebSocket connected successfully",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
                logger.debug(f"🏓 Pong sent to {user_id}")
            elif data.startswith("{"):
                try:
                    message = json.loads(data)
                    if message.get("type") == "mark_read":
                        notification_id = message.get("notification_id")
                        logger.debug(f"Mark read: {notification_id}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {user_id}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"👋 WebSocket disconnected normally: {user_id}")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"❌ WebSocket error for {user_id}: {e}", exc_info=True)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_total_connections(),
        "connected_users": manager.get_connected_users(),
        "status": "operational",
    }
