"""WebSocket endpoints for real-time notifications."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.websocket.manager import connection_manager

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time notifications.

    Path Parameters:
        - user_id: User ID

    Message Format (from client):
        {
            "type": "subscribe" | "unsubscribe" | "ping",
            "channel": "notifications" | "activities" | "payments" (optional)
        }

    Message Format (to client):
        {
            "type": "notification" | "activity" | "payment" | "pong",
            "data": {...},
            "timestamp": "2026-01-26T12:00:00Z"
        }
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            logger.warning(f"WebSocket connection attempt for non-existent user {user_id}")
            return

        # Connect user
        if not await connection_manager.connect(user_id, websocket):
            await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Failed to connect")
            return

        logger.info(f"WebSocket connected for user {user_id}")

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type", "ping")
                channel = data.get("channel", "notifications")

                if message_type == "subscribe":
                    # Subscribe to channel
                    connection_manager.subscribe_user(user_id, channel)
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "channel": channel,
                            "message": f"Subscribed to {channel}",
                        }
                    )
                    logger.info(f"User {user_id} subscribed to channel {channel}")

                elif message_type == "unsubscribe":
                    # Unsubscribe from channel
                    connection_manager.unsubscribe_user(user_id, channel)
                    await websocket.send_json(
                        {
                            "type": "unsubscribed",
                            "channel": channel,
                            "message": f"Unsubscribed from {channel}",
                        }
                    )
                    logger.info(f"User {user_id} unsubscribed from channel {channel}")

                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send_json(
                        {
                            "type": "pong",
                            "message": "pong",
                        }
                    )

                else:
                    logger.warning(f"Unknown message type from user {user_id}: {message_type}")

        except WebSocketDisconnect:
            await connection_manager.disconnect(user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")

        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await connection_manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")


@router.get("/api/websocket/status")
async def get_websocket_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get WebSocket connection status for user.

    Returns:
        - connected: Whether user is connected via WebSocket
        - subscriptions: List of subscribed channels
        - active_connections: Total active connections (admin only)
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        is_connected = connection_manager.is_user_connected(user_id)
        subscriptions = connection_manager.get_user_subscriptions(user_id) or []

        response = {
            "connected": is_connected,
            "subscriptions": list(subscriptions),
        }

        # Add active connections count for admins
        if user.is_admin:
            response["active_connections"] = connection_manager.get_active_connections_count()
            response["active_users"] = connection_manager.get_active_users()

        logger.info(f"WebSocket status retrieved for user {user_id}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving WebSocket status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve WebSocket status")


@router.post("/api/websocket/broadcast")
async def broadcast_notification(
    user_id: str = Depends(get_current_user_id),
    target_user_id: Optional[str] = Query(None, description="Target user ID (admin only)"),
    channel: str = Query("notifications", description="Channel to broadcast to"),
    message_type: str = Query("notification", description="Message type"),
    title: str = Query(..., description="Notification title"),
    content: str = Query(..., description="Notification content"),
    db: Session = Depends(get_db),
):
    """Broadcast a notification via WebSocket (admin only).

    Query Parameters:
        - target_user_id: Specific user to send to (if not provided, broadcasts to all)
        - channel: Channel to broadcast to
        - message_type: Type of message
        - title: Notification title
        - content: Notification content

    Returns:
        - success: Whether broadcast was successful
        - recipients: Number of recipients
    """
    try:
        # Verify user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        message = {
            "type": message_type,
            "channel": channel,
            "title": title,
            "content": content,
        }

        if target_user_id:
            # Send to specific user
            success = await connection_manager.broadcast_to_user(target_user_id, message)
            recipients = 1 if success else 0
            logger.info(f"Admin {user_id} sent notification to user {target_user_id}")
        else:
            # Broadcast to all users on channel
            recipients = await connection_manager.broadcast_to_channel(channel, message)
            logger.info(f"Admin {user_id} broadcasted notification to {recipients} users on channel {channel}")

        return {
            "success": recipients > 0,
            "recipients": recipients,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")
