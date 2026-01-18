"""
Verification Status Polling Service
Handles real-time status updates for pending verifications
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio
import logging

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
        """
        Poll verification status from TextVerified API
        """
        try:
            # Get verification from database
            verification = (
                self.db.query(Verification).filter(Verification.id == verification_id).first()
            )

            if not verification:
                raise HTTPException(status_code=404, detail="Verification not found")

            # Skip polling if already completed
            if verification.status in ["completed", "failed", "cancelled"]:
                return {
                    "id": verification.id,
                    "status": verification.status,
                    "phone_number": verification.phone_number,
                    "sms_code": verification.sms_code,
                    "sms_text": verification.sms_text,
                    "updated_at": (
                        verification.updated_at.isoformat() if verification.updated_at else None
                    ),
                }

            # Poll TextVerified API for status update
            if verification.activation_id:
                try:
                    tv_status = await self.textverified.get_verification_status(
                        verification.activation_id
                    )

                    # Update database with new status
                    old_status = verification.status
                    verification.status = tv_status.get("status", verification.status)
                    verification.sms_code = tv_status.get("sms_code") or verification.sms_code
                    verification.sms_text = tv_status.get("sms_text") or verification.sms_text
                    verification.updated_at = datetime.utcnow()

                    self.db.commit()

                    # Log status change
                    if old_status != verification.status:
                        logger.info(
                            f"Verification {verification_id} status changed: {old_status} -> {verification.status}"
                        )

                except Exception as e:
                    logger.error(f"TextVerified API polling failed for {verification_id}: {e}")

            return {
                "id": verification.id,
                "status": verification.status,
                "phone_number": verification.phone_number,
                "sms_code": verification.sms_code,
                "sms_text": verification.sms_text,
                "service_name": verification.service_name,
                "created_at": verification.created_at.isoformat(),
                "updated_at": (
                    verification.updated_at.isoformat() if verification.updated_at else None
                ),
            }

        except Exception as e:
            logger.error(f"Status polling failed for {verification_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Status polling failed: {str(e)}")

    async def poll_user_verifications(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Poll status for all pending verifications for a user
        """
        try:
            # Get all pending verifications for user
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
                    # Include current status even if polling failed
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
    """
    Get real-time verification status with polling
    """
    status_service = VerificationStatusService(db)

    # Verify user owns this verification
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == current_user.id)
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    return await status_service.poll_verification_status(verification_id)


@router.get("/status-updates")
async def get_status_updates(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get status updates for all user's pending verifications
    """
    status_service = VerificationStatusService(db)
    updates = await status_service.poll_user_verifications(current_user.id)

    return {"updates": updates, "count": len(updates), "timestamp": datetime.utcnow().isoformat()}


@router.post("/refresh-status/{verification_id}")
async def force_status_refresh(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Force refresh verification status from TextVerified API
    """
    status_service = VerificationStatusService(db)

    # Verify user owns this verification
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == current_user.id)
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    result = await status_service.poll_verification_status(verification_id)

    return {
        "message": "Status refreshed successfully",
        "data": result,
        "refreshed_at": datetime.utcnow().isoformat(),
    }
