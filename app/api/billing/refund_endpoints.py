"""Refund endpoints for managing payment refunds."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.services.refund_service import RefundService

logger = get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["Refunds"])


# Request Models
class InitiateRefundRequest(BaseModel):
    """Request model for initiating refund."""

    payment_id: str = Field(..., description="Payment ID to refund")
    reason: str = Field(..., description="Refund reason")


@router.post("/refund")
async def initiate_refund(
    request: InitiateRefundRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Initiate a refund request.

    Args:
        request: Refund request with payment_id and reason

    Returns:
        Refund details with reference

    Raises:
        400: Invalid request
        404: Payment not found
        500: Internal server error
    """
    try:
        refund_service = RefundService(db)
        refund = refund_service.initiate_refund(
            user_id=user_id,
            payment_id=request.payment_id,
            reason=request.reason,
            initiated_by="user",
        )

        logger.info(f"Refund initiated: {refund.reference} for user {user_id}")

        return {
            "reference": refund.reference,
            "status": refund.status,
            "amount": refund.amount,
            "reason": refund.reason,
            "initiated_at": (refund.initiated_at.isoformat() if refund.initiated_at else None),
        }

    except ValueError as e:
        logger.warning(f"Refund validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initiate refund: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate refund",
        )


@router.get("/refund/{reference}")
async def get_refund_status(
    reference: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get refund status.

    Args:
        reference: Refund reference

    Returns:
        Refund details

    Raises:
        404: Refund not found
        500: Internal server error
    """
    try:
        refund_service = RefundService(db)
        result = refund_service.verify_refund(reference)

        logger.info(f"Retrieved refund status: {reference}")

        return result

    except ValueError as e:
        logger.warning(f"Refund not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get refund status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve refund status",
        )


@router.get("/refunds")
async def get_refund_history(
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """Get refund history for user.

    Query Parameters:
        - skip: Number of records to skip (pagination)
        - limit: Number of records to return (max 100)

    Returns:
        - total: Total number of refunds
        - skip: Number of records skipped
        - limit: Number of records returned
        - refunds: List of refunds
    """
    try:
        refund_service = RefundService(db)
        result = refund_service.get_refund_history(user_id=user_id, skip=skip, limit=limit)

        logger.info(f"Retrieved {len(result['refunds'])} refunds for user {user_id}")

        return result

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get refund history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve refund history",
        )


@router.post("/refund/{reference}/cancel")
async def cancel_refund(
    reference: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel a pending refund.

    Args:
        reference: Refund reference

    Returns:
        Cancellation confirmation

    Raises:
        400: Cannot cancel refund
        404: Refund not found
        500: Internal server error
    """
    try:
        refund_service = RefundService(db)
        refund = refund_service.cancel_refund(reference, user_id)

        logger.info(f"Refund cancelled: {reference}")

        return {
            "reference": refund.reference,
            "status": refund.status,
            "message": "Refund cancelled successfully",
        }

    except ValueError as e:
        logger.warning(f"Refund cancellation error: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel refund: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel refund",
        )
