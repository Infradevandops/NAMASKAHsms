"""Payment endpoints for billing operations."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.payment import PaymentInitialize, PaymentInitializeResponse, PaymentVerify, PaymentVerifyResponse
from app.services.payment_service import get_payment_service
from app.middleware.rate_limiting import limiter

logger = get_logger(__name__)
router = APIRouter()


@router.post("/initialize", response_model=PaymentInitializeResponse)
@limiter.limit("5/minute")
async def initialize_payment(
    request: Request,
    payment_request: PaymentInitialize,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Initialize a payment transaction."""
    try:
        # Validate idempotency key if provided
        if idempotency_key:
            try:
                uuid.UUID(idempotency_key)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid idempotency key format (must be UUID)")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        payment_service = get_payment_service(db)
        result = await payment_service.initialize_payment(
            user_id=user_id,
            email=user.email,
            amount_usd=payment_request.amount_usd,
            idempotency_key=idempotency_key
        )

        return PaymentInitializeResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Payment initialization failed: {e}")
        raise HTTPException(status_code=500, detail="Payment initialization failed")


@router.post("/verify", response_model=PaymentVerifyResponse)
@limiter.limit("10/minute")
async def verify_payment(
    request: Request,
    payment_request: PaymentVerify,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verify a payment transaction."""
    try:
        payment_service = get_payment_service(db)
        result = await payment_service.verify_payment(payment_request.reference)

        if result.get("status") == True and result.get("data", {}).get("status") == "success":
            # Credit user account
            metadata = result.get("data", {}).get("metadata", {})
            amount = metadata.get("namaskah_amount", 0)
            
            if amount > 0:
                success = payment_service.credit_user(user_id, amount, payment_request.reference)
                if success:
                    user = db.query(User).filter(User.id == user_id).first()
                    return PaymentVerifyResponse(
                        status="success",
                        amount_credited=amount,
                        new_balance=user.credits if user else 0,
                        reference=payment_request.reference,
                        message="Payment verified and credited successfully"
                    )

        return PaymentVerifyResponse(
            status="failed",
            amount_credited=0,
            new_balance=0,
            reference=payment_request.reference,
            message="Payment verification failed"
        )

    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.get("/methods")
async def get_payment_methods(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get available payment methods."""
    try:
        return {
            "methods": [
                {
                    "name": "paystack",
                    "display_name": "Paystack",
                    "supported_currencies": ["USD", "NGN"],
                    "min_amount": 5.0,
                    "max_amount": 10000.0,
                    "enabled": True
                }
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get payment methods: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment methods")


@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook events."""
    try:
        # Get signature from header
        signature = request.headers.get("x-paystack-signature")
        if not signature:
            logger.warning("Webhook received without signature")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        # Get raw body
        body = await request.body()
        
        # Verify signature
        payment_service = get_payment_service(db)
        if not payment_service.verify_webhook_signature(body, signature):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse and process
        data = json.loads(body)
        event = data.get("event")
        
        if event == "charge.success":
            # Extract payment details
            payment_data = data.get("data", {})
            reference = payment_data.get("reference")
            
            if not reference:
                raise HTTPException(status_code=400, detail="Missing reference")
            
            # Get user info from metadata
            metadata = payment_data.get("metadata", {})
            user_id = metadata.get("user_id")
            amount = metadata.get("namaskah_amount", 0)
            
            if user_id and amount > 0:
                # Process with distributed lock
                await payment_service.credit_user_with_lock(user_id, amount, reference)
                logger.info(f"Webhook processed: {reference}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
