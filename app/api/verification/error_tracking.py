"""
Error tracking and transaction monitoring endpoints.
Captures detailed error information for analytics and debugging.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.purchase_outcome import PurchaseOutcome
from app.models.user import User
from app.models.verification import Verification
from app.services.auto_refund_service import AutoRefundService

router = APIRouter()


class ErrorReportRequest(BaseModel):
    failure_reason: str
    failure_category: str
    provider_error_code: str | None = None
    outcome_category: str
    error_message: str
    timestamp: str


class SMSReceiptRequest(BaseModel):
    sms_code: str
    received_at: str
    latency_seconds: float | None = None


class TimeoutReportRequest(BaseModel):
    timeout_at: str
    elapsed_seconds: int
    failure_reason: str
    failure_category: str
    refund_eligible: bool


class CancellationRequest(BaseModel):
    reason: str
    category: str
    cancelled_at: str
    cancelled_by: str


@router.post("/verification/{verification_id}/error")
async def report_verification_error(
    verification_id: str,
    error_info: ErrorReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report detailed error information for a verification."""
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
    verification.sms_received = False
    verification.refund_eligible = error_info.failure_category in [
        "provider_issue",
        "network_issue",
        "system_error",
    ]

    # Update purchase_outcome
    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == verification_id)
        .first()
    )

    if outcome:
        outcome.outcome_category = error_info.outcome_category
        outcome.provider_error_code = error_info.provider_error_code
        outcome.sms_received = False

    db.commit()

    return {
        "status": "error_recorded",
        "failure_category": error_info.failure_category,
        "refund_eligible": verification.refund_eligible,
    }


@router.post("/verification/{verification_id}/sms-received")
async def confirm_sms_received(
    verification_id: str,
    receipt_data: SMSReceiptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm SMS code was received by user."""
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
    verification.completed_at = datetime.now(timezone.utc)

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
        "latency_seconds": receipt_data.latency_seconds,
    }


@router.post("/verification/{verification_id}/timeout")
async def report_timeout(
    verification_id: str,
    timeout_data: TimeoutReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report verification timeout and trigger automatic refund."""
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
    verification.failure_reason = timeout_data.failure_reason
    verification.failure_category = timeout_data.failure_category
    verification.refund_eligible = timeout_data.refund_eligible
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
    refund_service = AutoRefundService(db)
    refund_result = await refund_service.process_verification_refund(
        verification_id, "timeout"
    )

    return {
        "status": "timeout_recorded",
        "refund_initiated": refund_result is not None,
        "refund_amount": refund_result.get("refund_amount") if refund_result else None,
    }


@router.post("/verification/{verification_id}/cancel")
async def cancel_verification_enhanced(
    verification_id: str,
    cancel_data: CancellationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel verification with detailed tracking."""
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
    verification.failure_category = cancel_data.category
    verification.sms_received = False

    # Update purchase_outcome
    outcome = (
        db.query(PurchaseOutcome)
        .filter(PurchaseOutcome.verification_id == verification_id)
        .first()
    )

    if outcome:
        outcome.sms_received = False
        outcome.outcome_category = (
            "PRODUCT" if cancel_data.category == "user_action" else "SYSTEM"
        )

    db.commit()

    # Trigger refund if eligible
    refund_initiated = False
    if cancel_data.category == "user_action":
        refund_service = AutoRefundService(db)
        refund_result = await refund_service.process_verification_refund(
            verification_id, cancel_data.reason
        )
        refund_initiated = refund_result is not None

    return {
        "status": "cancelled",
        "reason": cancel_data.reason,
        "refund_initiated": refund_initiated,
    }
