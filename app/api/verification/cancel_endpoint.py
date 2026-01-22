"""Verification cancellation endpoint with automatic refund."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.verification import Verification
from app.services.auto_refund_service import AutoRefundService
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/{verification_id}/cancel")
async def cancel_verification(
    verification_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel a pending verification and issue automatic refund.
    
    Only pending verifications can be cancelled.
    Credits are automatically refunded to the user's account.
    """
    
    # Get verification
    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id,
            Verification.user_id == user_id,
        )
        .first()
    )
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Check if can be cancelled
    if verification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel verification with status: {verification.status}",
        )
    
    try:
        # Cancel with TextVerified if activation_id exists
        if verification.activation_id:
            tv_service = TextVerifiedService()
            try:
                await tv_service.cancel_verification(verification.activation_id)
                logger.info(f"Cancelled TextVerified activation: {verification.activation_id}")
            except Exception as tv_error:
                logger.warning(f"TextVerified cancellation failed: {tv_error}")
        
        # Update status
        verification.status = "cancelled"
        db.commit()
        
        # Process automatic refund
        refund_service = AutoRefundService(db)
        refund_result = refund_service.process_verification_refund(
            verification_id, "cancelled"
        )
        
        if refund_result:
            logger.info(
                f"Verification {verification_id} cancelled with refund: "
                f"${refund_result['refund_amount']:.2f}"
            )
            return {
                "success": True,
                "message": "Verification cancelled and refunded",
                "verification_id": verification_id,
                "refund_amount": refund_result["refund_amount"],
                "new_balance": refund_result["new_balance"],
            }
        else:
            logger.warning(f"Refund failed for cancelled verification {verification_id}")
            return {
                "success": True,
                "message": "Verification cancelled (refund pending)",
                "verification_id": verification_id,
            }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Cancellation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel verification",
        )
