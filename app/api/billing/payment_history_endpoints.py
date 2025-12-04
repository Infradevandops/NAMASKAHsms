"""Payment history and management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.services.payment_service import PaymentService
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/billing", tags=["Billing"])


@router.get("/history")
async def get_payment_history(
    user_id: str = Depends(get_current_user_id),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: pending, success, failed, refunded"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get payment history for user.
    
    Query Parameters:
        - status: Filter by payment status (optional)
        - skip: Number of records to skip (pagination)
        - limit: Number of records to return (max 100)
    
    Returns:
        - total: Total number of payments
        - skip: Number of records skipped
        - limit: Number of records returned
        - payments: List of payments with details
    """
    try:
        payment_service = PaymentService(db)
        history = payment_service.get_payment_history(
            user_id=user_id,
            status=status_filter,
            skip=skip,
            limit=limit
        )
        
        logger.info(
            f"Retrieved payment history for user {user_id}: "
            f"{len(history['payments'])} payments"
        )
        
        return history
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get payment history for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment history"
        )


@router.get("/summary")
async def get_payment_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get payment summary for user.
    
    Returns:
        - current_balance: Current credit balance
        - total_paid: Total amount paid
        - total_credited: Total credits received
        - successful_payments: Number of successful payments
        - failed_payments: Number of failed payments
        - pending_payments: Number of pending payments
        - total_payments: Total number of payments
    """
    try:
        payment_service = PaymentService(db)
        summary = payment_service.get_payment_summary(user_id)
        
        logger.info(f"Generated payment summary for user {user_id}")
        
        return summary
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get payment summary for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment summary"
        )


@router.post("/refund")
async def refund_payment(
    reference: str = Query(..., description="Payment reference to refund"),
    reason: str = Query("User requested refund", description="Refund reason"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Refund a payment (admin only).
    
    Query Parameters:
        - reference: Payment reference to refund
        - reason: Reason for refund (optional)
    
    Returns:
        - reference: Payment reference
        - status: Refund status
        - amount_refunded: Amount refunded
        - new_balance: New credit balance
        - reason: Refund reason
        - timestamp: Refund timestamp
    """
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            logger.warning(f"Non-admin user {user_id} attempted to refund payment")
            raise HTTPException(status_code=403, detail="Admin access required")
        
        payment_service = PaymentService(db)
        result = payment_service.refund_payment(
            reference=reference,
            user_id=user_id,
            reason=reason
        )
        
        logger.info(f"Refunded payment: {reference}")
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to refund payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refund payment"
        )


@router.get("/payment/{reference}")
async def get_payment_details(
    reference: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get details for a specific payment.
    
    Path Parameters:
        - reference: Payment reference
    
    Returns:
        - reference: Payment reference
        - amount_usd: Amount in USD
        - amount_ngn: Amount in NGN
        - status: Payment status
        - credited: Whether credits were added
        - payment_method: Payment method
        - created_at: Payment creation timestamp
        - webhook_received: Whether webhook was received
    """
    try:
        from app.models.transaction import PaymentLog
        
        # Get payment log
        payment_log = db.query(PaymentLog).filter(
            PaymentLog.reference == reference,
            PaymentLog.user_id == user_id
        ).first()
        
        if not payment_log:
            logger.warning(f"Payment not found: {reference}")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        logger.info(f"Retrieved payment details: {reference}")
        
        return {
            "reference": payment_log.reference,
            "amount_usd": payment_log.amount_usd,
            "amount_ngn": payment_log.amount_ngn,
            "status": payment_log.status,
            "credited": payment_log.credited,
            "payment_method": payment_log.payment_method,
            "created_at": payment_log.created_at.isoformat() if payment_log.created_at else None,
            "webhook_received": payment_log.webhook_received,
            "email": payment_log.email
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment details"
        )


@router.post("/initiate")
async def initiate_payment_v2(
    amount_usd: float = Query(..., gt=0, description="Amount in USD"),
    description: str = Query("Credit purchase", description="Payment description"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Initiate a payment transaction (v2 with service).
    
    Query Parameters:
        - amount_usd: Amount in USD (must be positive)
        - description: Payment description (optional)
    
    Returns:
        - reference: Payment reference
        - authorization_url: Paystack authorization URL
        - access_code: Paystack access code
        - amount_usd: Amount in USD
        - amount_ngn: Amount in NGN
        - status: Payment status
        - created_at: Payment creation timestamp
    """
    try:
        payment_service = PaymentService(db)
        result = payment_service.initiate_payment(
            user_id=user_id,
            amount_usd=amount_usd,
            description=description
        )
        
        logger.info(f"Initiated payment for user {user_id}: ${amount_usd}")
        
        return result
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initiate payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )


@router.post("/verify/{reference}")
async def verify_payment_v2(
    reference: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Verify a payment transaction (v2 with service).
    
    Path Parameters:
        - reference: Payment reference to verify
    
    Returns:
        - reference: Payment reference
        - status: Payment status
        - amount_usd: Amount in USD
        - amount_ngn: Amount in NGN
        - credited: Whether credits were added
        - paid_at: Payment timestamp
        - verified_at: Verification timestamp
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.verify_payment(
            reference=reference,
            user_id=user_id
        )
        
        logger.info(f"Verified payment: {reference}")
        
        return result
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to verify payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        )
