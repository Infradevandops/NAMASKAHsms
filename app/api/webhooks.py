"""Webhook endpoints for SMS notifications"""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.verification import Verification

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature from 5SIM"""
    if not signature or not secret:
        return False

    try:
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant time comparison)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}")
        return False


@router.post("/5sim/sms")
async def receive_5sim_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    db: Session = Depends(get_db)
):
    """
    Receive SMS webhook from 5SIM

    This endpoint receives instant notifications when SMS arrives,
    eliminating the need for polling and providing real-time updates.

    Expected payload from 5SIM:
    {
        "id": 123456789,
        "phone": "+1234567890",
        "operator": "verizon",
        "product": "telegram",
        "price": 0.75,
        "status": "RECEIVED",
        "sms": [
            {
                "text": "Your verification code is: 123456",
                "code": "123456",
                "date": "2024-01-20T10:00:00Z"
            }
        ],
        "created_at": "2024-01-20T09:55:00Z",
        "expires": "2024-01-20T10:10:00Z"
    }
    """
    try:
        # Get raw body for signature verification
        body = await request.body()

        # Verify webhook signature (if configured)
        settings = get_settings()
        webhook_secret = getattr(settings, "fivesim_webhook_secret", None)

        if webhook_secret and x_signature:
            if not verify_webhook_signature(body, x_signature, webhook_secret):
                logger.warning("Invalid webhook signature received")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature",
                )

        # Parse JSON payload
        data = await request.json()

        # Extract activation ID
        activation_id = data.get("id")
        if not activation_id:
            logger.error("Webhook missing activation ID")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing activation ID",
            )

        # Find verification by activation ID
        verification = (
            db.query(Verification)
            .filter(Verification.verification_code == str(activation_id))
            .first()
        )

        if not verification:
            logger.warning(f"Verification not found for activation {activation_id}")
            # Return 200 to prevent 5SIM from retrying
            return {"success": True, "message": "Verification not found (may be already processed)"}

        # Check if already completed
        if verification.status == "completed":
            logger.info(f"Verification {verification.id} already completed")
            return {
                "success": True,
                "message": "Verification already completed"
            }

        # Extract SMS data
        sms_list = data.get("sms", [])
        if not sms_list:
            logger.warning(f"Webhook for {activation_id} has no SMS data")
            return {"success": True, "message": "No SMS data in webhook"}

        # Get latest SMS
        latest_sms = sms_list[-1] if isinstance(sms_list, list) else sms_list
        sms_text = latest_sms.get("text", "") if isinstance(latest_sms, dict) else str(latest_sms)

        # Extract verification code from SMS text
        # TextVerified provides the code directly in the webhook
        extracted_code = latest_sms.get("code") if isinstance(latest_sms, dict) else None

        if not extracted_code:
            # Try to extract code from text (common patterns: "Your code is 123456" or "Code: 123456")
            import re

            matches = re.findall(r"\b(\d{4,8})\b", sms_text)
            if matches:
                extracted_code = matches[-1]  # Take the last match

        # Update verification status
        verification.status = "completed"
        verification.completed_at = datetime.now(timezone.utc)

        # Store SMS data if fields exist
        if hasattr(verification, "sms_text"):
            verification.sms_text = sms_text
        if hasattr(verification, "sms_code"):
            verification.sms_code = extracted_code

        db.commit()

        logger.info(f"Webhook processed for verification {verification.id}")

        return {
            "success": True,
            "message": "Webhook processed successfully",
            "verification_id": verification.id,
            "code": extracted_code,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # Return 200 to prevent 5SIM from retrying on our internal errors
        return {"success": False, "message": "Internal error processing webhook", "error": str(e)}


@router.get("/5sim/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook is accessible"""
    return {
        "success": True,
        "message": "Webhook endpoint is accessible",
        "endpoint": "/webhooks/sms",
        "method": "POST",
        "note": "Configure this URL in your SMS provider dashboard",
    }


@router.post("/sms/test")
async def test_webhook_processing(request: Request, db: Session = Depends(get_db)):
    """
    Test webhook processing with sample data

    Use this endpoint to test webhook functionality without a live SMS provider
    """
    try:
        data = await request.json()

        # Validate test payload
        if "id" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test payload must include 'id' field",
            )

        activation_id = data["id"]

        # Find verification
        verification = (
            db.query(Verification)
            .filter(Verification.verification_code == str(activation_id))
            .first()
        )

        if not verification:
            return {
                "success": False,
                "message": f"No verification found with activation ID {activation_id}",
                "note": "Create a verification first, then use its activation_id for testing",
            }

        return {
            "success": True,
            "message": "Test webhook would process this verification",
            "verification": {
                "id": verification.id,
                "service": verification.service_name,
                "phone": verification.phone_number,
                "status": verification.status,
                "activation_id": activation_id,
            },
            "note": "This is a test endpoint. Real webhooks use POST /webhooks/sms",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}",
        )
