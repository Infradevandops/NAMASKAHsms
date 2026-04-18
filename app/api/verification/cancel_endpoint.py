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
router = APIRouter(tags=["Verification"])


@router.post("/cancel/{verification_id}")
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

    if verification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel verification with status: {verification.status}",
        )

    try:
        # 1. Cancel on provider side
        if verification.activation_id:
            from app.services.providers.provider_router import ProviderRouter

            p_router = ProviderRouter()

            # Use appropriate adapter
            adapter = None
            if verification.provider == "textverified":
                from app.services.providers.textverified_adapter import (
                    TextVerifiedAdapter,
                )

                adapter = TextVerifiedAdapter()
            elif verification.provider == "telnyx":
                from app.services.providers.telnyx_adapter import TelnyxAdapter

                adapter = TelnyxAdapter()
            elif verification.provider == "5sim":
                from app.services.providers.fivesim_adapter import FiveSimAdapter

                adapter = FiveSimAdapter()
            elif verification.provider == "pvapins":
                from app.services.providers.pvapins_adapter import PVAPinsAdapter

                adapter = PVAPinsAdapter()

            if adapter:
                try:
                    await adapter.cancel(verification.activation_id)
                    logger.info(
                        f"Cancelled {verification.provider} activation: {verification.activation_id}"
                    )
                except Exception as provider_error:
                    logger.warning(
                        f"Provider cancellation failed for {verification.provider}: {provider_error}"
                    )

        # 2. Mark as failed in DB
        from app.services.verification_status_service import (
            mark_verification_cancelled_by_user,
        )

        mark_verification_cancelled_by_user(db, verification)

        # 3. Process refund immediately
        refund_service = AutoRefundService(db)
        refund_result = await refund_service.process_verification_refund(
            verification_id, "cancelled"
        )

        if refund_result:
            logger.info(
                f"Verification {verification_id} cancelled with refund: ${refund_result['refund_amount']:.2f}"
            )
            return {
                "success": True,
                "message": "Verification cancelled and refunded",
                "verification_id": verification_id,
                "refund_amount": refund_result["refund_amount"],
                "new_balance": refund_result["new_balance"],
            }
        else:
            logger.warning(
                f"Refund failed for cancelled verification {verification_id}"
            )
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
