"""SMS forwarding configuration API."""

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
    """Configure SMS forwarding settings."""
    try:
        # Get or create config
        config = (
            db.query(ForwardingConfig)
            .filter(ForwardingConfig.user_id == user_id)
            .first()
        )

        if not config:
            config = ForwardingConfig(user_id=user_id)
            db.add(config)

        # Update settings
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

        # Test email forwarding
        if config.email_enabled and config.email_address:
            try:
                email_sent = await _send_forwarding_email(
                    email_address=config.email_address,
                    sms_data={
                        "message": test_message,
                        "phone_number": "+1234567890",
                        "service": "Test Service",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "is_test": True,
                    },
                )

                results.append(
                    {
                        "type": "email",
                        "success": email_sent,
                        "message": (
                            f"Test email sent to {config.email_address}"
                            if email_sent
                            else "Email service not configured or failed"
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Email test failed: {str(e)}")
                results.append(
                    {
                        "type": "email",
                        "success": False,
                        "message": f"Email test failed: {str(e)}",
                    }
                )

        # Test webhook forwarding
        if config.webhook_enabled and config.webhook_url:
            try:
                webhook_sent = await _send_forwarding_webhook(
                    webhook_url=config.webhook_url,
                    webhook_secret=config.webhook_secret,
                    sms_data={
                        "message": test_message,
                        "phone_number": "+1234567890",
                        "service": "Test Service",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "is_test": True,
                    },
                )

                results.append(
                    {
                        "type": "webhook",
                        "success": webhook_sent,
                        "message": (
                            f"Test webhook posted to {config.webhook_url}"
                            if webhook_sent
                            else "Webhook delivery failed"
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Webhook test failed: {str(e)}")
                results.append(
                    {
                        "type": "webhook",
                        "success": False,
                        "message": f"Webhook test failed: {str(e)}",
                    }
                )

        if not results:
            raise HTTPException(status_code=400, detail="No forwarding methods enabled")

        return {
            "success": any(r["success"] for r in results),
            "message": "Forwarding test completed",
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test forwarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _send_forwarding_email(email_address: str, sms_data: dict) -> bool:
    """Send SMS forwarding email.

    Args:
        email_address: Recipient email address
        sms_data: SMS message data

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        subject = "SMS Forwarding - New Message Received"
        if sms_data.get("is_test"):
            subject = "SMS Forwarding - Test Message"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">SMS Message Received</h2>

                    {f'<p style="background: #fef3c7; padding: 10px; border-radius: 4px; border-left: 4px solid #f59e0b;"><strong>⚠️ This is a test message</strong></p>' if sms_data.get("is_test") else ''}

                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Message Details</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Phone Number:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{sms_data.get('phone_number', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Service:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{sms_data.get('service', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Received:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{sms_data.get('timestamp', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;" colspan="2">
                                    <strong>Message:</strong>
                                    <div style="background: white; padding: 15px; margin-top: 10px; border-radius: 4px; border: 1px solid #e5e7eb;">
                                        {sms_data.get('message', 'No message content')}
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                        This is an automated SMS forwarding notification from Namaskah SMS.
                        To manage your forwarding settings, visit your dashboard.
                    </p>
                </div>
            </body>
        </html>
        """

        # Use existing email service
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = email_service.from_email
        message["To"] = email_address

        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Send via SMTP
        if email_service.enabled:
            import asyncio

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, email_service._send_smtp, email_address, message.as_string()
            )
            logger.info(f"SMS forwarding email sent to {email_address}")
            return True
        else:
            logger.warning("Email service not configured")
            return False

    except Exception as e:
        logger.error(f"Failed to send forwarding email: {str(e)}")
        return False


async def _send_forwarding_webhook(
    webhook_url: str, webhook_secret: str, sms_data: dict
) -> bool:
    """Send SMS forwarding webhook.

    Args:
        webhook_url: Webhook URL
        webhook_secret: Webhook secret for signing
        sms_data: SMS message data

    Returns:
        True if webhook sent successfully, False otherwise
    """
    try:
        # Prepare payload
        payload = {
            "event": "sms.received",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": sms_data,
        }

        payload_json = json.dumps(payload)

        # Generate signature if secret provided
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Namaskah-SMS-Forwarding/1.0",
        }

        if webhook_secret:
            signature = hmac.new(
                webhook_secret.encode(), payload_json.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature
            headers["X-Webhook-Signature-Algorithm"] = "sha256"

        # Send webhook with retry logic
        max_retries = 3
        timeout = 10.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        webhook_url, content=payload_json, headers=headers
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        logger.info(f"SMS forwarding webhook sent to {webhook_url}")
                        return True
                    else:
                        logger.warning(
                            f"Webhook returned status {response.status_code}"
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2**attempt)  # Exponential backoff
                            continue
                        return False

            except httpx.TimeoutException:
                logger.warning(f"Webhook timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False
            except httpx.RequestError as e:
                logger.error(f"Webhook request error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False

        return False

    except Exception as e:
        logger.error(f"Failed to send forwarding webhook: {str(e)}")
        return False


async def forward_sms_message(user_id: str, sms_data: dict, db: Session) -> dict:
    """Forward SMS message to configured destinations.

    This function should be called when a new SMS is received.

    Args:
        user_id: User ID
        sms_data: SMS message data
        db: Database session

    Returns:
        Dictionary with forwarding results
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

        # Forward via email
        if config.email_enabled and config.email_address:
            email_sent = await _send_forwarding_email(config.email_address, sms_data)
            results.append({"type": "email", "success": email_sent})

        # Forward via webhook
        if config.webhook_enabled and config.webhook_url:
            webhook_sent = await _send_forwarding_webhook(
                config.webhook_url, config.webhook_secret, sms_data
            )
            results.append({"type": "webhook", "success": webhook_sent})

        return {
            "forwarded": True,
            "results": results,
            "success_count": sum(1 for r in results if r["success"]),
        }

    except Exception as e:
        logger.error(f"Failed to forward SMS: {str(e)}")
        return {"forwarded": False, "error": str(e)}
