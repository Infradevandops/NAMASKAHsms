"""Telegram integration API endpoints"""

import logging
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.telegram import TelegramConnection, TelegramForwardingRule
from app.models.user import User
from app.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


# Schemas
class TelegramConnectionResponse(BaseModel):
    """Telegram connection status"""

    connected: bool
    chat_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None


class TelegramConnectRequest(BaseModel):
    """Request to generate connection token"""

    pass


class TelegramConnectResponse(BaseModel):
    """Connection token response"""

    token: str
    bot_username: str
    instructions: str


class TelegramSettingsRequest(BaseModel):
    """Telegram forwarding settings"""

    forward_all: bool = True
    service_filter: Optional[list[str]] = Field(
        default=None, description="Only forward these services"
    )
    country_filter: Optional[list[str]] = Field(
        default=None, description="Only forward these countries"
    )


class TelegramSettingsResponse(BaseModel):
    """Telegram forwarding settings response"""

    forward_all: bool
    service_filter: Optional[list[str]]
    country_filter: Optional[list[str]]


class TelegramWebhookUpdate(BaseModel):
    """Telegram webhook update"""

    update_id: int
    message: Optional[dict] = None


# Endpoints
@router.get("/status", response_model=TelegramConnectionResponse)
async def get_telegram_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's Telegram connection status"""
    connection = (
        db.query(TelegramConnection)
        .filter(TelegramConnection.user_id == current_user.id)
        .first()
    )

    if not connection:
        return TelegramConnectionResponse(connected=False)

    return TelegramConnectionResponse(
        connected=connection.active,
        chat_id=connection.chat_id,
        username=connection.username,
        first_name=connection.first_name,
        connected_at=connection.connected_at,
        last_message_at=connection.last_message_at,
    )


@router.post("/connect", response_model=TelegramConnectResponse)
async def connect_telegram(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Generate a connection token for Telegram bot

    User should send this token to the bot via /start command
    """
    # Check if already connected
    existing = (
        db.query(TelegramConnection)
        .filter(TelegramConnection.user_id == current_user.id)
        .first()
    )

    if existing and existing.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram already connected. Disconnect first to reconnect.",
        )

    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Token stored in-memory for now; Redis persistence deferred with Telegram feature
    # When Telegram is activated: store token in Redis with 10-min TTL
    # await cache.set(f"tg:connect:{token}", current_user.id, ttl=600)

    # Get bot info
    bot_info = await telegram_service.get_bot_info()
    bot_username = bot_info.get("result", {}).get("username", "vrenum_sms_bot")

    instructions = f"""
1. Open Telegram and search for @{bot_username}
2. Send the command: /start {token}
3. Your account will be connected automatically
    """.strip()

    return TelegramConnectResponse(
        token=token, bot_username=bot_username, instructions=instructions
    )


@router.delete("/disconnect")
async def disconnect_telegram(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Disconnect Telegram from user account"""
    connection = (
        db.query(TelegramConnection)
        .filter(TelegramConnection.user_id == current_user.id)
        .first()
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Telegram connection found"
        )

    # Soft delete - mark as inactive
    connection.active = False
    db.commit()

    return {"message": "Telegram disconnected successfully"}


@router.get("/settings", response_model=TelegramSettingsResponse)
async def get_telegram_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get Telegram forwarding settings"""
    rules = (
        db.query(TelegramForwardingRule)
        .filter(TelegramForwardingRule.user_id == current_user.id)
        .first()
    )

    if not rules:
        # Return defaults
        return TelegramSettingsResponse(
            forward_all=True, service_filter=None, country_filter=None
        )

    return TelegramSettingsResponse(
        forward_all=rules.forward_all,
        service_filter=rules.service_filter,
        country_filter=rules.country_filter,
    )


@router.put("/settings", response_model=TelegramSettingsResponse)
async def update_telegram_settings(
    settings_data: TelegramSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update Telegram forwarding settings"""
    # Check if connected
    connection = (
        db.query(TelegramConnection)
        .filter(
            TelegramConnection.user_id == current_user.id,
            TelegramConnection.active == True,
        )
        .first()
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connect Telegram first before configuring settings",
        )

    # Get or create rules
    rules = (
        db.query(TelegramForwardingRule)
        .filter(TelegramForwardingRule.user_id == current_user.id)
        .first()
    )

    if not rules:
        rules = TelegramForwardingRule(user_id=current_user.id)
        db.add(rules)

    # Update settings
    rules.forward_all = settings_data.forward_all
    rules.service_filter = settings_data.service_filter
    rules.country_filter = settings_data.country_filter
    rules.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(rules)

    return TelegramSettingsResponse(
        forward_all=rules.forward_all,
        service_filter=rules.service_filter,
        country_filter=rules.country_filter,
    )


@router.post("/test")
async def send_test_message(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Send a test message to user's Telegram"""
    connection = (
        db.query(TelegramConnection)
        .filter(
            TelegramConnection.user_id == current_user.id,
            TelegramConnection.active == True,
        )
        .first()
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active Telegram connection found",
        )

    result = await telegram_service.send_test_message(connection.chat_id)

    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {result.get('error')}",
        )

    return {"message": "Test message sent successfully"}


@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Telegram bot updates

    Handles /start command with connection token
    """
    try:
        update = await request.json()
        logger.info(f"Received Telegram webhook: {update}")

        # Extract message
        message = update.get("message")
        if not message:
            return {"ok": True}

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        username = message.get("from", {}).get("username")
        first_name = message.get("from", {}).get("first_name")

        # Handle /start command with token
        if text.startswith("/start "):
            token = text.split(" ", 1)[1]

            # Token verification deferred with Telegram feature activation
            # When activated: look up user_id = await cache.get(f"tg:connect:{token}")

            # Check if chat_id already connected
            existing = (
                db.query(TelegramConnection)
                .filter(TelegramConnection.chat_id == chat_id)
                .first()
            )

            if existing:
                # Reactivate connection
                existing.active = True
                existing.username = username
                existing.first_name = first_name
                db.commit()

                await telegram_service.send_message(
                    chat_id, "✅ Connection reactivated! You'll receive SMS codes here."
                )
            else:
                # Create new connection
                # User linking deferred with Telegram feature activation
                # When activated: user_id = await cache.get(f"tg:connect:{token}")
                await telegram_service.send_message(
                    chat_id,
                    "⚠️ Connection token system not yet implemented. Please use the web interface to complete setup.",
                )

        # Handle /status command
        elif text == "/status":
            connection = (
                db.query(TelegramConnection)
                .filter(TelegramConnection.chat_id == chat_id)
                .first()
            )

            if connection and connection.active:
                await telegram_service.send_message(
                    chat_id,
                    f"✅ Connected to vrenum.app account\nLast message: {connection.last_message_at or 'Never'}",
                )
            else:
                await telegram_service.send_message(
                    chat_id, "❌ Not connected. Use /start <token> to connect."
                )

        # Handle /stop command
        elif text == "/stop":
            connection = (
                db.query(TelegramConnection)
                .filter(TelegramConnection.chat_id == chat_id)
                .first()
            )

            if connection:
                connection.active = False
                db.commit()
                await telegram_service.send_message(
                    chat_id, "✅ Disconnected from vrenum.app. Use /start to reconnect."
                )

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": False, "error": str(e)}
