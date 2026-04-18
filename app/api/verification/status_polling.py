"""Verification Status Polling Service
Handles real-time status updates for pending verifications
"""

import logging
from datetime import datetime, timedelta, timezone
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
        """Poll verification status from the correct provider API."""
        try:
            verification = (
                self.db.query(Verification)
                .filter(Verification.id == verification_id)
                .first()
            )

            if not verification:
                raise HTTPException(status_code=404, detail="Verification not found")

            # Calculate expiry (Phase 12: Elite Timer Sync)
            from app.core.config import settings

            timeout_minutes = getattr(settings, "sms_polling_max_minutes", 2)
            ends_at = None
            if verification.created_at:
                created_at = (
                    verification.created_at.replace(tzinfo=timezone.utc)
                    if verification.created_at.tzinfo is None
                    else verification.created_at
                )
                ends_at = created_at + timedelta(minutes=timeout_minutes)

            base_response = {
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
                "created_at": (
                    verification.created_at.isoformat()
                    if verification.created_at
                    else None
                ),
                "updated_at": (
                    verification.updated_at.isoformat()
                    if verification.updated_at
                    else None
                ),
                "failure_reason": verification.failure_reason,
                "failure_category": verification.failure_category,
                "ends_at": ends_at.isoformat() if ends_at else None,
                "server_time": datetime.now(timezone.utc).isoformat(),
            }

            if verification.status in ["completed", "failed", "cancelled", "timeout"]:
                return base_response

            if verification.activation_id:
                try:
                    # Multi-provider status bridge
                    provider = verification.provider or "textverified"
                    incoming_code = None
                    incoming_text = None
                    new_status = verification.status

                    if provider == "textverified":
                        tv_status = await self.textverified.get_verification_status(
                            verification.activation_id
                        )
                        incoming_code = tv_status.get("sms_code")
                        incoming_text = tv_status.get("sms_text")
                        new_status = tv_status.get("status", verification.status)
                    elif provider == "5sim":
                        from app.services.providers.fivesim_adapter import (
                            FiveSimAdapter,
                        )

                        adapter = FiveSimAdapter()
                        messages = await adapter.check_messages(
                            verification.activation_id
                        )
                        if messages:
                            incoming_code = messages[-1].code
                            incoming_text = messages[-1].text
                            new_status = "completed"
                    elif provider == "telnyx":
                        from app.services.providers.telnyx_adapter import TelnyxAdapter

                        adapter = TelnyxAdapter()
                        messages = await adapter.check_messages(
                            verification.activation_id
                        )
                        if messages:
                            incoming_code = messages[-1].code
                            incoming_text = messages[-1].text
                            new_status = "completed"

                    old_status = verification.status

                    if incoming_code and incoming_code != verification.sms_code:
                        # Success path
                        from app.services.verification_status_service import (
                            mark_sms_code_received,
                        )

                        await mark_sms_code_received(
                            self.db, verification, incoming_code, incoming_text
                        )
                    elif new_status != old_status:
                        verification.status = new_status
                        verification.updated_at = datetime.now(timezone.utc)
                        self.db.commit()

                    if old_status != verification.status:
                        logger.info(
                            f"Verification {verification_id} ({provider}) status changed: {old_status} -> {verification.status}"
                        )

                        # Terminal failure handling
                        if verification.status in ["failed", "timeout", "cancelled"]:
                            from app.services.auto_refund_service import (
                                AutoRefundService,
                            )

                            refund_service = AutoRefundService(self.db)
                            await refund_service.process_verification_refund(
                                verification_id, verification.status
                            )

                        # Update base_response with new status/text
                        base_response["status"] = verification.status
                        base_response["sms_code"] = verification.sms_code
                        base_response["sms_text"] = verification.sms_text
                        base_response["updated_at"] = (
                            verification.updated_at.isoformat()
                        )

                except Exception as e:
                    logger.error(
                        f"API polling failed for {verification_id} ({verification.provider}): {e}"
                    )

            return base_response

        except Exception as e:
            logger.error(f"Status polling failed for {verification_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Status polling failed: {str(e)}"
            )

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
