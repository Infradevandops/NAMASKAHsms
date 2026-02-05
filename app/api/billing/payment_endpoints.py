"""Payment endpoints for billing operations."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.payment import PaymentInitialize, PaymentInitializeResponse, PaymentVerify, PaymentVerifyResponse
from app.services.payment_service import get_payment_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    request: PaymentInitialize,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Initialize a payment transaction."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        payment_service = get_payment_service(db)
        result = await payment_service.initialize_payment(
            user_id=user_id,
            email=user.email,
            amount_usd=request.amount_usd
        )

        return PaymentInitializeResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Payment initialization failed: {e}")
        raise HTTPException(status_code=500, detail="Payment initialization failed")


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    request: PaymentVerify,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Verify a payment transaction."""
    try:
        payment_service = get_payment_service(db)
        result = await payment_service.verify_payment(request.reference)

        if result.get("status") == True and result.get("data", {}).get("status") == "success":
            # Credit user account
            metadata = result.get("data", {}).get("metadata", {})
            amount = metadata.get("namaskah_amount", 0)
            
            if amount > 0:
                success = payment_service.credit_user(user_id, amount, request.reference)
                if success:
                    user = db.query(User).filter(User.id == user_id).first()
                    return PaymentVerifyResponse(
                        status="success",
                        amount_credited=amount,
                        new_balance=user.credits if user else 0,
                        reference=request.reference,
                        message="Payment verified and credited successfully"
                    )

        return PaymentVerifyResponse(
            status="failed",
            amount_credited=0,
            new_balance=0,
            reference=request.reference,
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
