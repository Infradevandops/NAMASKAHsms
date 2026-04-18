"""Service for managing detailed verification status tracking."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import REASON_TO_CATEGORY, FailureCategory, FailureReason
from app.models.verification import Verification


def mark_verification_failed(
    db: Session,
    verification: Verification,
    reason: str,
    error_message: Optional[str] = None,
    refund_eligible: bool = True,
) -> None:
    """Mark verification as failed with detailed reason.

    Args:
        db: Database session
        verification: Verification object to update
        reason: FailureReason code (e.g., FailureReason.NUMBER_UNAVAILABLE)
        error_message: Optional detailed error message
        refund_eligible: Whether failure qualifies for refund
    """
    verification.status = "failed"
    verification.failure_reason = reason
    verification.failure_category = REASON_TO_CATEGORY.get(
        reason, FailureCategory.INTERNAL_ERROR
    )
    verification.error_message = error_message
    verification.refund_eligible = refund_eligible
    verification.sms_received = False
    verification.completed_at = datetime.now(timezone.utc)
    db.commit()


def mark_sms_code_received(
    db: Session,
    verification: Verification,
    sms_code: str,
    sms_text: str,
) -> None:
    """Mark SMS code as received and verification completed.

    Args:
        db: Database session
        verification: Verification object to update
        sms_code: The SMS code sent to user
        sms_text: Full SMS text
    """
    verification.sms_code = sms_code
    verification.sms_text = sms_text
    verification.sms_received = True
    verification.sms_received_at = datetime.now(timezone.utc)
    verification.status = "completed"
    verification.completed_at = datetime.now(timezone.utc)
    verification.refund_eligible = False  # No refund if SMS received
    verification.failure_reason = None
    verification.failure_category = None
    db.commit()


def mark_verification_cancelled_by_user(
    db: Session,
    verification: Verification,
) -> None:
    """Mark verification as cancelled by user."""
    mark_verification_failed(
        db,
        verification,
        reason=FailureReason.USER_CANCELLED,
        error_message="User cancelled verification",
        refund_eligible=True,
    )
