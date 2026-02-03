"""Consolidated verification endpoints - US only via TextVerified."""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationCreate, VerificationResponse
from app.services.textverified_service import TextVerifiedService
from app.services.notification_dispatcher import NotificationDispatcher

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])

# DEPLOYMENT VERIFICATION: Notification system v2.0 - 2026-01-24 04:50 UTC
NOTIFICATION_SYSTEM_VERSION = "2.0.0"


@router.get("/services")
async def get_available_services():
    """Get available services from TextVerified API (US only)."""
    logger.info(f"🔔 NOTIFICATION SYSTEM VERSION: {NOTIFICATION_SYSTEM_VERSION}")
    try:
        tv_service = TextVerifiedService()
        
        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        services_data = await tv_service.get_services_list()
        return {
            "success": True,
            "services": services_data,
            "total": len(services_data),
            "country": "US",
            "provider": "TextVerified"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Services fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch services from TextVerified API")


@router.get("/area-codes")
async def get_area_codes():
    """Get available US area codes."""
    try:
        tv_service = TextVerifiedService()
        
        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        area_codes_data = await tv_service.get_area_codes_list()
        return {
            "success": True,
            "area_codes": area_codes_data,
            "total": len(area_codes_data),
            "country": "US",
            "provider": "TextVerified"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Area codes fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch area codes")


@router.post("/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new verification (US numbers only)."""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check user balance
        if user.credits < 2.50:  # Minimum cost for verification
            raise HTTPException(status_code=402, detail="Insufficient credits")

        # Initialize TextVerified service
        tv_service = TextVerifiedService()
        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        # Purchase number from TextVerified (US only)
        purchase_result = await tv_service.purchase_number(
            service=verification_data.service,
            area_code=getattr(verification_data, 'area_code', None),
            carrier=getattr(verification_data, 'carrier', None)
        )

        if not purchase_result.get("success"):
            raise HTTPException(status_code=400, detail=purchase_result.get("error", "Failed to purchase number"))

        # Create verification record
        verification = Verification(
            user_id=user_id,
            service=verification_data.service,
            phone_number=purchase_result["phone_number"],
            status="pending",
            cost=purchase_result["cost"],
            provider="TextVerified",
            country="US",
            created_at=datetime.utcnow()
        )

        db.add(verification)
        
        # Deduct cost from user balance
        user.credits -= purchase_result["cost"]
        
        db.commit()
        db.refresh(verification)

        # Send notification
        try:
            dispatcher = NotificationDispatcher(db)
            await dispatcher.notify_verification_started(
                user_id=user_id,
                verification_id=verification.id,
                service=verification.service,
                phone_number=verification.phone_number,
                cost=verification.cost
            )
        except Exception as e:
            logger.warning(f"Notification failed: {e}")

        logger.info(f"Verification created: {verification.id} for user {user_id}")

        return VerificationResponse(
            id=verification.id,
            service=verification.service,
            phone_number=verification.phone_number,
            status=verification.status,
            cost=verification.cost,
            country="US",
            provider="TextVerified",
            created_at=verification.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create verification")


@router.get("/{verification_id}/sms")
async def get_verification_sms(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get SMS for a verification."""
    try:
        # Get verification
        verification = db.query(Verification).filter(
            Verification.id == verification_id,
            Verification.user_id == user_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Get SMS from TextVerified
        tv_service = TextVerifiedService()
        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        sms_result = await tv_service.get_sms(verification_id)
        
        if sms_result.get("success") and sms_result.get("sms"):
            # Update verification status
            verification.status = "completed"
            verification.sms_content = sms_result["sms"]
            verification.completed_at = datetime.utcnow()
            db.commit()

            # Send notification
            try:
                dispatcher = NotificationDispatcher(db)
                await dispatcher.notify_verification_completed(
                    user_id=user_id,
                    verification_id=verification.id,
                    service=verification.service,
                    phone_number=verification.phone_number
                )
            except Exception as e:
                logger.warning(f"Notification failed: {e}")

        return {
            "success": sms_result.get("success", False),
            "sms": sms_result.get("sms"),
            "code": sms_result.get("code"),
            "status": verification.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get SMS")


@router.delete("/{verification_id}")
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel a verification."""
    try:
        # Get verification
        verification = db.query(Verification).filter(
            Verification.id == verification_id,
            Verification.user_id == user_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        if verification.status != "pending":
            raise HTTPException(status_code=400, detail="Can only cancel pending verifications")

        # Cancel with TextVerified
        tv_service = TextVerifiedService()
        if tv_service.enabled:
            await tv_service.cancel_verification(verification_id)

        # Update status
        verification.status = "cancelled"
        verification.completed_at = datetime.utcnow()
        
        # Refund user (partial refund for cancellation)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            refund_amount = verification.cost * 0.5  # 50% refund for cancellation
            user.credits += refund_amount

        db.commit()

        logger.info(f"Verification cancelled: {verification_id}")

        return {
            "success": True,
            "message": "Verification cancelled",
            "refund_amount": refund_amount
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel verification")