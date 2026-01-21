"""Consolidated SMS Verification API."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.services.tier_manager import TierManager
from app.core.tier_helpers import raise_tier_error

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])


class SuccessResponse(BaseModel):
    message: str
    data: dict = {}


class VerificationCreate(BaseModel):
    service_name: str
    country: str = "US"
    capability: str = "sms"
    area_code: Optional[str] = None
    carrier: Optional[str] = None


class VerificationResponse(BaseModel):
    id: str
    service_name: str
    phone_number: str
    capability: str
    status: str
    cost: float
    created_at: str
    completed_at: Optional[str] = None


class VerificationHistoryResponse(BaseModel):
    verifications: list
    total_count: int


def create_safe_error_detail(e):
    return str(e)[:100]


@router.get("/services")
async def get_available_services():
    """Get available services from TextVerified API."""
    try:
        from app.services.textverified_service import TextVerifiedService

        tv_service = TextVerifiedService()

        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        services_data = await tv_service.get_services()
        return {
            "success": True,
            "services": services_data.get("services", []),
            "total": len(services_data.get("services", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Services fetch error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch services from TextVerified API"
        )


@router.post(
    "/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED
)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification."""
    try:
        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        base_cost = 0.50

        if current_user.free_verifications > 0:
            # Free verifications don't support custom filters normally
            if verification_data.area_code or verification_data.carrier:
                 if current_user.credits < 1.0: # Buffer for premium features
                     raise HTTPException(status_code=402, detail="Premium filters require credits even for free users")
            current_user.free_verifications -= 1
            db.commit()
        elif current_user.credits >= base_cost:
            current_user.credits -= base_cost
            db.commit()
        else:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        # Tier-based feature gating
        tier_manager = TierManager(db)
        if verification_data.area_code and not tier_manager.check_feature_access(user_id, "area_code_selection"):
            user_tier = tier_manager.get_user_tier(user_id)
            raise_tier_error(user_tier, "payg", user_id)
            
        if verification_data.carrier and not tier_manager.check_feature_access(user_id, "isp_filtering"):
            user_tier = tier_manager.get_user_tier(user_id)
            raise_tier_error(user_tier, "pro", user_id)

        # Get TextVerified service
        from app.services.textverified_service import TextVerifiedService

        tv_service = TextVerifiedService()

        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        # Purchase number from TextVerified with optional filters
        result = await tv_service.create_verification(
            service=verification_data.service_name,
            area_code=verification_data.area_code,
            carrier=verification_data.carrier
        )

        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=verification_data.capability,
            status="pending",
            cost=result["cost"],
            phone_number=result["phone_number"],
            country=verification_data.country,
            activation_id=result["id"], # Adjusted to match create_verification result keys
            provider="textverified",
            requested_area_code=verification_data.area_code,
            requested_carrier=verification_data.carrier
        )

        db.add(verification)
        db.commit()
        db.refresh(verification)

        logger.info(f"Verification created: {verification.id}")
        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at.isoformat(),
            "completed_at": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification creation failed: {create_safe_error_detail(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create verification")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status."""
    try:
        verification = (
            db.query(Verification).filter(Verification.id == verification_id).first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at.isoformat(),
            "completed_at": (
                verification.completed_at.isoformat()
                if verification.completed_at
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status fetch error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch verification status"
        )


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get verification history."""
    try:
        verifications = (
            db.query(Verification).filter(Verification.user_id == user_id).all()
        )

        return VerificationHistoryResponse(
            verifications=[],
            total_count=len(verifications),
        )
    except Exception as e:
        logger.error(f"History fetch error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch verification history"
        )


@router.get("/{verification_id}/status")
async def get_verification_status_polling(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get verification status for polling."""
    try:
        verification = (
            db.query(Verification)
            .filter(Verification.id == verification_id, Verification.user_id == user_id)
            .first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Check if SMS received via TextVerified
        if verification.status == "pending" and verification.activation_id:
            from app.services.textverified_service import TextVerifiedService

            tv_service = TextVerifiedService()

            try:
                sms_result = await tv_service.get_sms(verification.activation_id)
                if sms_result and sms_result.get("sms_code"):
                    verification.sms_code = sms_result["sms_code"]
                    verification.sms_text = sms_result.get("sms_text", "")
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(
                        f"SMS received for verification {verification_id}: {sms_result['sms_code']}"
                    )
            except Exception as e:
                logger.warning(f"SMS check failed for {verification_id}: {e}")

        return {
            "verification_id": verification.id,
            "status": verification.status,
            "phone_number": verification.phone_number,
            "sms_code": verification.sms_code,
            "sms_text": verification.sms_text,
            "cost": verification.cost,
            "created_at": verification.created_at.isoformat(),
            "completed_at": (
                verification.completed_at.isoformat()
                if verification.completed_at
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to check verification status"
        )


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and release number."""
    try:
        verification = (
            db.query(Verification)
            .filter(Verification.id == verification_id, Verification.user_id == user_id)
            .first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Release number via TextVerified if still active
        if verification.activation_id and verification.status == "pending":
            try:
                from app.services.textverified_service import TextVerifiedService

                tv_service = TextVerifiedService()
                await tv_service.cancel_number(verification.activation_id)
                logger.info(f"Released TextVerified number for {verification_id}")
            except Exception as e:
                logger.warning(f"Failed to release number for {verification_id}: {e}")

        verification.status = "cancelled"
        db.commit()
        logger.info(f"Verification cancelled: {verification_id}")

        return SuccessResponse(message="Verification cancelled")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancellation error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel verification")
