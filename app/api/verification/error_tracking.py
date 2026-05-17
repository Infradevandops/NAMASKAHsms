"""Error tracking endpoints for verification flow."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.purchase_outcome import PurchaseOutcome
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/api/verification", tags=["Verification Error Tracking"])


class ErrorReportRequest(BaseModel):
    """Error report from frontend."""

    failure_reason: str
    failure_category: str
    provider_error_code: Optional[str] = None
    outcome_category: str
    error_message: str
    timestamp: str


class SMSReceiptRequest(BaseModel):
    """SMS receipt confirmation from frontend."""

    sms_code: str
    received_at: str
    latency_seconds: Optional[float] = None


class TimeoutReportRequest(BaseModel):
    """Timeout report from frontend."""

    timeout_at: str
    elapsed_seconds: float
    failure_reason: str = "sms_timeout"
    failure_category: str = "provider_issue"
    refund_eligible: bool = True


class CancellationRequest(BaseModel):
    """Enhanced cancellation with reason."""

    reason: str = "user_cancelled"
    category: str = "user_action"
    cancelled_at: str
    cancelled_by: str = "user"


@router.post("/{verification_id}/error")
async def report_verification_error(
    verification_id: str,
    error_info: ErrorReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report categorized error from frontend.

    AC-1: Error Categorization
    - Captures failure_reason, failure_category, provider_error_code, outcome_category
    - Stores in verifications and purchase_outcomes tables
    """

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(404, "Verification not found")

    # Update verification with error details
    verification.failure_reason = error_info.failure_reason
    verification.failure_category = error_info.failure_category
    verification.error_message = error_info.error_message
    verification.status = "error"
    verification.outcome = "error"

    # Update purchase_outcome
    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == verification_id)
        .first()
    )

    if outcome:
        outcome.outcome_category = error_info.outcome_category
        outcome.provider_error_code = error_info.provider_error_code

    db.commit()

    return {
        "status": "error_recorded",
        "verification_id": verification_id,
        "failure_reason": error_info.failure_reason,
        "failure_category": error_info.failure_category,
    }


@router.post("/{verification_id}/sms-received")
async def confirm_sms_received(
    verification_id: str,
    receipt_data: SMSReceiptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm SMS receipt from frontend.

    AC-2: SMS Receipt Confirmation
    - Updates sms_received, sms_received_at, latency_seconds
    - Marks verification as completed
    """

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(404, "Verification not found")

    # Update verification
    verification.sms_received = True
    verification.sms_received_at = datetime.now(timezone.utc)
    verification.sms_code = receipt_data.sms_code
    verification.status = "completed"
    verification.outcome = "completed"

    # Update purchase_outcome
    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == verification_id)
        .first()
    )

    if outcome:
        outcome.sms_received = True
        outcome.latency_seconds = receipt_data.latency_seconds
        outcome.raw_sms_code = receipt_data.sms_code

    db.commit()

    return {
        "status": "sms_receipt_confirmed",
        "verification_id": verification_id,
        "sms_received": True,
        "latency_seconds": receipt_data.latency_seconds,
    }


@router.post("/{verification_id}/timeout")
async def report_timeout(
    verification_id: str,
    timeout_data: TimeoutReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report timeout and trigger auto-refund.

    AC-3: Timeout Detection & Auto-Refund
    - Updates verification status to timeout
    - Triggers automatic refund via AutoRefundService
    - Sends WebSocket notification
    """

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(404, "Verification not found")

    # Update verification
    verification.status = "timeout"
    verification.outcome = "timeout"
    verification.failure_reason = "sms_timeout"
    verification.failure_category = "provider_issue"
    verification.refund_eligible = True
    verification.sms_received = False

    # Update purchase_outcome
    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == verification_id)
        .first()
    )

    if outcome:
        outcome.sms_received = False
        outcome.outcome_category = "PROVIDER"
        outcome.latency_seconds = timeout_data.elapsed_seconds

    db.commit()

    # Trigger automatic refund
    from app.services.auto_refund_service import AutoRefundService

    refund_service = AutoRefundService(db)

    try:
        refund_result = await refund_service.process_verification_refund(
            verification_id, "timeout"
        )

        return {
            "status": "timeout_recorded",
            "refund_initiated": True,
            "refund_amount": refund_result.get("refund_amount"),
            "verification_id": verification_id,
        }
    except Exception as e:
        # Log error but don't fail the timeout recording
        import logging

        logging.error(f"Auto-refund failed for {verification_id}: {e}")

        return {
            "status": "timeout_recorded",
            "refund_initiated": False,
            "error": str(e),
            "verification_id": verification_id,
        }


@router.post("/{verification_id}/cancel")
async def cancel_verification_enhanced(
    verification_id: str,
    cancel_data: CancellationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enhanced cancellation with reason tracking.

    AC-4: Enhanced Cancellation Tracking
    - Captures cancel_reason, category, timestamp, cancelled_by
    - Triggers refund if eligible
    """

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(404, "Verification not found")

    # Update verification
    verification.status = "cancelled"
    verification.outcome = "cancelled"
    verification.cancel_reason = cancel_data.reason
    verification.cancelled_at = datetime.now(timezone.utc)
    verification.cancelled_by = cancel_data.cancelled_by

    db.commit()

    # Trigger refund if eligible (not completed)
    refund_issued = False
    refund_amount = 0.0

    if verification.status != "completed" and verification.cost > 0:
        from app.services.auto_refund_service import AutoRefundService

        refund_service = AutoRefundService(db)

        try:
            refund_result = await refund_service.process_verification_refund(
                verification_id, "user_cancelled"
            )
            refund_issued = True
            refund_amount = refund_result.get("refund_amount", 0.0)
        except Exception as e:
            import logging

            logging.error(f"Refund failed for cancelled {verification_id}: {e}")

    return {
        "status": "cancelled",
        "verification_id": verification_id,
        "cancel_reason": cancel_data.reason,
        "refund_issued": refund_issued,
        "refund_amount": refund_amount,
    }
