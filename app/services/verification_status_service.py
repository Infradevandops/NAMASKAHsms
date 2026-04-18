"""Service for managing detailed verification status tracking."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import REASON_TO_CATEGORY, FailureCategory, FailureReason
from app.models.verification import Verification


async def mark_verification_failed(
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

    # Critical Fix: Process refund if eligible (Phase 12: Atomic Integrity)
    if refund_eligible and not getattr(verification, "refunded", False):
        from app.services.auto_refund_service import AutoRefundService

        try:
            # Create refund service
            refund_service = AutoRefundService(db)
            # Await the refund process directly for atomic completion
            await refund_service.process_verification_refund(verification.id, reason)
        except Exception as e:
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to process atomic refund for {verification.id}: {e}")

    db.commit()


async def mark_sms_code_received(
    db: Session,
    verification: Verification,
    sms_code: str,
    sms_text: str,
    transcription: Optional[str] = None,
    audio_url: Optional[str] = None,
) -> None:
    """Mark SMS/Voice verification completed.

    Args:
        db: Database session
        verification: Verification object to update
        sms_code: The SMS code or transcription result
        sms_text: Full SMS text or transcription text
        transcription: Optional raw transcription (for voice)
        audio_url: Optional audio link (for voice)
    """
    verification.sms_code = sms_code
    verification.sms_text = sms_text
    verification.sms_received = True
    verification.sms_received_at = datetime.now(timezone.utc)
    verification.status = "completed"
    verification.completed_at = datetime.now(timezone.utc)
    verification.refund_eligible = False  # No refund if message received
    verification.failure_reason = None
    verification.failure_category = None

    # Store voice metadata
    if transcription:
        verification.transcription = transcription
    if audio_url:
        verification.audio_url = audio_url

    db.commit()


async def mark_verification_transcribing(
    db: Session, verification: Verification, audio_url: Optional[str] = None
) -> None:
    """Mark voice verification as transcribing (Phase 6 Mastery)."""
    verification.status = "transcribing"
    if audio_url:
        verification.audio_url = audio_url
    db.commit()


async def mark_verification_cancelled_by_user(
    db: Session,
    verification: Verification,
) -> None:
    """Mark verification as cancelled by user."""
    await mark_verification_failed(
        db,
        verification,
        reason=FailureReason.USER_CANCELLED,
        error_message="User cancelled verification",
        refund_eligible=True,
    )
