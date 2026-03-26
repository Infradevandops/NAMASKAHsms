"""SMS forwarding configuration API — email and webhook active, Telegram coming soon."""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.forwarding import ForwardingConfig
from app.services.email_service import email_service

logger = get_logger(__name__)

router = APIRouter(prefix="/forwarding", tags=["Forwarding"])


@router.post("/configure")
async def configure_forwarding(
    email_enabled: bool = False,
    email_address: str = None,
    webhook_enabled: bool = False,
    webhook_url: str = None,
    webhook_secret: str = None,
    forward_all: bool = True,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Configure SMS forwarding — email and webhook supported."""
    try:
        config = (
            db.query(ForwardingConfig)
            .filter(ForwardingConfig.user_id == user_id)
            .first()
        )

        if not config:
            config = ForwardingConfig(user_id=user_id)
            db.add(config)

        config.email_enabled = email_enabled
        config.email_address = email_address
        config.webhook_enabled = webhook_enabled
        config.webhook_url = webhook_url
        config.webhook_secret = webhook_secret
        config.forward_all = forward_all
        config.is_active = email_enabled or webhook_enabled

        db.commit()

        return {
            "success": True,
            "message": "Forwarding configured successfully",
            "config": {
                "email_enabled": config.email_enabled,
                "email_address": config.email_address,
                "webhook_enabled": config.webhook_enabled,
                "webhook_url": config.webhook_url,
                "forward_all": config.forward_all,
                "is_active": config.is_active,
                "telegram_enabled": False,
                "telegram_status": "coming_soon",
            },
        }

    except Exception as e:
        logger.error(f"Failed to configure forwarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_forwarding_config(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get forwarding configuration."""
    try:
        config = (
            db.query(ForwardingConfig)
            .filter(ForwardingConfig.user_id == user_id)
            .first()
        )

        if not config:
            return {
                "success": True,
                "configured": False,
                "message": "No forwarding configured",
                "available_methods": ["email", "webhook"],
                "coming_soon": ["telegram"],
            }

        return {
            "success": True,
            "configured": True,
            "config": {
                "email_enabled": config.email_enabled,
                "email_address": config.email_address,
                "webhook_enabled": config.webhook_enabled,
                "webhook_url": config.webhook_url,
                "forward_all": config.forward_all,
                "is_active": config.is_active,
                "telegram_enabled": False,
                "telegram_status": "coming_soon",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get forwarding config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_forwarding(
    test_message: str = "Test SMS forwarding",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Test forwarding configuration."""
    try:
        config = (
            db.query(ForwardingConfig)
            .filter(ForwardingConfig.user_id == user_id)
            .first()
        )

        if not config or not config.is_active:
            raise HTTPException(status_code=400, detail="Forwarding not configured")

        results = []
        sms_data = {
            "message": test_message,
            "phone_number": "+1234567890",
            "service": "Test Service",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_test": True,
        }

        if config.email_enabled and config.email_address:
            sent = await _send_forwarding_email(config.email_address, sms_data)
            results.append({
                "type": "email",
                "success": sent,
                "message": f"Test email sent to {config.email_address}" if sent else "Email delivery failed",
            })

        if config.webhook_enabled and config.webhook_url:
            sent = await _send_forwarding_webhook(config.webhook_url, config.webhook_secret, sms_data)
            results.append({
                "type": "webhook",
                "success": sent,
                "message": f"Test webhook posted to {config.webhook_url}" if sent else "Webhook delivery failed",
            })

        if not results:
            raise HTTPException(status_code=400, detail="No forwarding methods enabled")

        return {
            "success": any(r["success"] for r in results),
            "results": results,
            "note": "Telegram forwarding coming soon",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test forwarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _send_forwarding_email(email_address: str, sms_data: dict) -> bool:
    """Forward SMS to email using the active email service (Resend or SMTP)."""
    try:
        subject = "SMS Forwarding — Test Message" if sms_data.get("is_test") else "SMS Forwarding — New Message"
        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#667eea;">SMS Message Received</h2>
            <div style="background:#f9fafb;padding:20px;border-radius:8px;margin:20px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;"><strong>Phone:</strong></td>
                        <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{sms_data.get('phone_number','N/A')}</td></tr>
                    <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb;"><strong>Service:</strong></td>
                        <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{sms_data.get('service','N/A')}</td></tr>
                    <tr><td style="padding:8px;"><strong>Message:</strong></td>
                        <td style="padding:8px;">{sms_data.get('message','No content')}</td></tr>
                </table>
            </div>
            <p style="color:#999;font-size:12px;">Sent via Namaskah SMS Forwarding</p>
        </div></body></html>
        """
        return await email_service._send(email_address, subject, html_body)
    except Exception as e:
        logger.error(f"Forwarding email failed: {e}")
        return False


async def _send_forwarding_webhook(webhook_url: str, webhook_secret: str, sms_data: dict) -> bool:
    """Forward SMS to webhook URL with HMAC signature."""
    try:
        payload = json.dumps({
            "event": "sms.received",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": sms_data,
        })

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Namaskah-SMS-Forwarding/1.0",
        }

        if webhook_secret:
            sig = hmac.new(webhook_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = sig

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(webhook_url, content=payload, headers=headers)
                    if resp.status_code in [200, 201, 202, 204]:
                        return True
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
            except (httpx.TimeoutException, httpx.RequestError) as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        return False
    except Exception as e:
        logger.error(f"Forwarding webhook failed: {e}")
        return False


async def forward_sms_message(user_id: str, sms_data: dict, db: Session) -> dict:
    """
    Forward a received SMS to all configured destinations for a user.
    Called by sms_polling_service after an OTP is received.
    Telegram forwarding is not yet implemented — placeholder returns coming_soon.
    """
    try:
        config = (
            db.query(ForwardingConfig)
            .filter(ForwardingConfig.user_id == user_id)
            .first()
        )

        if not config or not config.is_active:
            return {"forwarded": False, "reason": "Forwarding not configured"}

        results = []

        if config.email_enabled and config.email_address:
            sent = await _send_forwarding_email(config.email_address, sms_data)
            results.append({"type": "email", "success": sent})

        if config.webhook_enabled and config.webhook_url:
            sent = await _send_forwarding_webhook(config.webhook_url, config.webhook_secret, sms_data)
            results.append({"type": "webhook", "success": sent})

        # Telegram — coming soon, not yet implemented
        # results.append({"type": "telegram", "success": False, "status": "coming_soon"})

        return {
            "forwarded": len(results) > 0,
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
        }

    except Exception as e:
        logger.error(f"Failed to forward SMS: {e}")
        return {"forwarded": False, "error": str(e)}
