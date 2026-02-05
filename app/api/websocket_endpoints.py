"""WebSocket endpoints for real-time notifications."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import manager
from app.core.logging import get_logger
import jwt
from app.core.config import get_settings

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])
settings = get_settings()


async def authenticate_websocket(token: str) -> str:
    """Authenticate WebSocket connection and return user_id."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("No user_id in token")

        return user_id

    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
    except Exception as e:
        raise ValueError(f"Authentication failed: {str(e)}")


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket, token: str = Query(..., description="JWT token for authentication")
):
    """WebSocket endpoint for real-time notifications.
    
    Usage:
        ws://localhost:8000/ws/notifications?token=YOUR_JWT_TOKEN
    """
    user_id = None

    try:
        # Authenticate user from token
        user_id = await authenticate_websocket(token)
        logger.info(f"🔐 WebSocket auth successful: {user_id}")

    except Exception as e:
        logger.error(f"❌ WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Connect
    await manager.connect(websocket, user_id)

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "connected",
                "message": "WebSocket connected successfully",
                "user_id": user_id,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
                logger.debug(f"🏓 Pong sent to {user_id}")

            # Handle other messages (future expansion)
            elif data.startswith("{"):
                # JSON message
                import json

                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "mark_read":
                        # Handle mark notification as read
                        notification_id = message.get("notification_id")
                        logger.debug(f"Mark read: {notification_id}")

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {user_id}: {data}")

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