"""TextVerified webhook handlers for real-time updates."""
from app.core.logging import get_logger
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verify TextVerified webhook signature using HMAC-SHA512."""
    try:
        secret = settings.textverified_api_key.encode()
        expected_signature = hmac.new(
            secret, request_body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


@router.post("/textverified/sms-received")
async def handle_sms_received(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle SMS received webhook from TextVerified."""
    try:
        # Get signature from headers
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")

        # Get request body
        body = await request.body()

        # Verify signature
        if not verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        import json

        data = json.loads(body)
        event_type = data.get("event")

        if event_type == "v2.sms.received":
            payload = data.get("data", {})
            reservation_id = payload.get("reservationId")
            sms_text = payload.get("text")
            from_number = payload.get("from")
            received_at = payload.get("receivedAt")

            # Find rental
            rental = db.query(Rental).filter(
                Rental.external_id == reservation_id
            ).first()

            if rental:
                # Store SMS message
                sms = SMSMessage(
                    user_id=rental.user_id,
                    rental_id=rental.id,
                    from_number=from_number,
                    text=sms_text,
                    external_id=payload.get("id"),
                    received_at=datetime.fromisoformat(
                        received_at.replace("Z", "+00:00")
                    ) if received_at else datetime.utcnow(),
                    is_read=False,
                )
                db.add(sms)
                db.commit()

                logger.info(f"SMS received for rental {reservation_id}")

        return {"success": True}

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/textverified/billing-cycle-renewed")
async def handle_billing_cycle_renewed(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle billing cycle renewal webhook from TextVerified."""
    try:
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")

        body = await request.body()

        if not verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")


        data = json.loads(body)
        event_type = data.get("event")

        if event_type == "v2.rental.billingcycle.renewed":
            payload = data.get("data", {})
            reservation_id = payload.get("reservationId")
            new_expiry = payload.get("expiresAt")

            # Find rental
            rental = db.query(Rental).filter(
                Rental.external_id == reservation_id
            ).first()

            if rental:
                # Update expiry date
                rental.expires_at = datetime.fromisoformat(
                    new_expiry.replace("Z", "+00:00")
                )
                db.commit()

                logger.info(f"Billing cycle renewed for rental {reservation_id}")

        return {"success": True}

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/textverified/verification-completed")
async def handle_verification_completed(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle verification completed webhook from TextVerified."""
    try:
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")

        body = await request.body()

        if not verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")


        data = json.loads(body)
        event_type = data.get("event")

        if event_type == "v2.verification.completed":
            payload = data.get("data", {})
            verification_id = payload.get("id")
            status = payload.get("status")

            # Find verification
            verification = db.query(Verification).filter(
                Verification.external_id == verification_id
            ).first()

            if verification:
                # Update status
                verification.status = status
                db.commit()

                logger.info(f"Verification completed: {verification_id}")

        return {"success": True}

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
