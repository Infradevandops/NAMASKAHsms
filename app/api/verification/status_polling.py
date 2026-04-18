"""Verification Status Polling Service
Handles real-time status updates for pending verifications
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verification", tags=["verification-status"])


class VerificationStatusService:

    def __init__(self, db: Session):
        self.db = db
        self.textverified = TextVerifiedService()

    async def poll_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Poll verification status from TextVerified API."""
        try:
            verification = (
                self.db.query(Verification)
                .filter(Verification.id == verification_id)
                .first()
            )

            if not verification:
                raise HTTPException(status_code=404, detail="Verification not found")

            if verification.status in ["completed", "failed", "cancelled"]:
                return {
                    "id": verification.id,
                    "status": verification.status,
                    "phone_number": verification.phone_number,
                    "sms_code": verification.sms_code,
                    "sms_text": verification.sms_text,
                    "assigned_carrier": verification.assigned_carrier,
                    "assigned_area_code": verification.assigned_area_code,
                    "requested_carrier": verification.requested_carrier,
                    "requested_area_code": verification.requested_area_code,
                    "fallback_applied": verification.fallback_applied,
                    "same_state_fallback": verification.same_state_fallback,
                    "updated_at": (
                        verification.updated_at.isoformat()
                        if verification.updated_at
                        else None
                    ),
                    "failure_reason": verification.failure_reason,
                    "failure_category": verification.failure_category,
                }

            if verification.activation_id:
                try:
                    tv_status = await self.textverified.get_verification_status(
                        verification.activation_id
                    )

                    old_status = verification.status

                    # Only accept sms_code if it arrived AFTER this verification
                    # was created — prevents stale codes from recycled numbers
                    incoming_code = tv_status.get("sms_code")
                    incoming_text = tv_status.get("sms_text")

                    if incoming_code and incoming_code != verification.sms_code:
                        # Validate freshness via check_sms which applies created_after
                        fresh = await self.textverified.check_sms(
                            verification.activation_id,
                            created_after=verification.created_at,
                        )
                        if fresh.get("status") == "COMPLETED":
                            verification.sms_code = incoming_code
                            verification.sms_text = incoming_text
                            verification.status = "completed"
                        # else: stale code — do not update
                    else:
                        verification.status = tv_status.get(
                            "status", verification.status
                        )

                    verification.updated_at = datetime.now(timezone.utc)
                    self.db.commit()

                    if old_status != verification.status:
                        logger.info(
                            f"Verification {verification_id} status changed: {old_status} -> {verification.status}"
                        )

                except Exception as e:
                    logger.error(
                        f"TextVerified API polling failed for {verification_id}: {e}"
                    )

            return {
                "id": verification.id,
                "status": verification.status,
                "phone_number": verification.phone_number,
                "sms_code": verification.sms_code,
                "sms_text": verification.sms_text,
                "service_name": verification.service_name,
                "assigned_carrier": verification.assigned_carrier,
                "assigned_area_code": verification.assigned_area_code,
                "requested_carrier": verification.requested_carrier,
                "requested_area_code": verification.requested_area_code,
                "fallback_applied": verification.fallback_applied,
                "same_state_fallback": verification.same_state_fallback,
                "created_at": verification.created_at.isoformat(),
                "updated_at": (
                    verification.updated_at.isoformat()
                    if verification.updated_at
                    else None
                ),
                "failure_reason": verification.failure_reason,
                "failure_category": verification.failure_category,
            }

        except Exception as e:
            logger.error(f"Status polling failed for {verification_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Status polling failed: {str(e)}"
            )

    async def poll_user_verifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Poll status for all pending verifications for a user."""
        try:
            pending_verifications = (
                self.db.query(Verification)
                .filter(
                    Verification.user_id == user_id,
                    Verification.status.in_(["pending", "processing"]),
                )
                .all()
            )

            results = []
            for verification in pending_verifications:
                try:
                    status_data = await self.poll_verification_status(verification.id)
                    results.append(status_data)
                except Exception as e:
                    logger.error(f"Failed to poll verification {verification.id}: {e}")
                    results.append(
                        {
                            "id": verification.id,
                            "status": verification.status,
                            "phone_number": verification.phone_number,
                            "error": str(e),
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"User verification polling failed for {user_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"User verification polling failed: {str(e)}"
            )


@router.get("/status/{verification_id}")
async def get_verification_status(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get real-time verification status with polling."""
    status_service = VerificationStatusService(db)

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    return await status_service.poll_verification_status(verification_id)


@router.get("/status-updates")
async def get_status_updates(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get status updates for all user's pending verifications."""
    status_service = VerificationStatusService(db)
    updates = await status_service.poll_user_verifications(current_user.id)

    return {
        "updates": updates,
        "count": len(updates),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/refresh-status/{verification_id}")
async def force_status_refresh(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Force refresh verification status from TextVerified API."""
    status_service = VerificationStatusService(db)

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id, Verification.user_id == current_user.id
        )
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    result = await status_service.poll_verification_status(verification_id)

    return {
        "message": "Status refreshed successfully",
        "data": result,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }
