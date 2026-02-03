"""Consolidated SMS Verification API."""


import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.tier_helpers import raise_tier_error
from app.models.user import User
from app.models.verification import Verification
from app.services.tier_manager import TierManager
from app.services.textverified_service import TextVerifiedService
from app.models.transaction import Transaction
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.textverified_service import TextVerifiedService
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_service import NotificationService

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])

# DEPLOYMENT VERIFICATION: Notification system v2.0 - 2026-01-24 04:50 UTC
NOTIFICATION_SYSTEM_VERSION = "2.0.0"


class SuccessResponse(BaseModel):

    message: str
    data: dict = {}


class VerificationCreate(BaseModel):

    service_name: str
    country: str = "US"
    capability: str = "sms"
    area_code: Optional[str] = None
    carrier: Optional[str] = None
    idempotency_key: Optional[str] = None


class VerificationResponse(BaseModel):

    id: str
    service_name: str
    phone_number: str
    capability: str
    status: str
    cost: float
    created_at: str
    completed_at: Optional[str] = None
    fallback_applied: bool = False
    sms_code: Optional[str] = None
    sms_text: Optional[str] = None
    carrier: Optional[str] = None


class VerificationHistoryResponse(BaseModel):

    verifications: List[VerificationResponse]
    total_count: int


    def create_safe_error_detail(e):

        """Sanitize error messages to prevent sensitive data leakage."""
        msg = str(e)[:100]
    # Remove common sensitive patterns
        msg = re.sub(
        r"(password|api_key|secret|token|auth)\s*[=:]\s*\S+",
        r"\1=***",
        msg,
        flags=re.IGNORECASE,
        )
        return msg


        @router.get("/services")
    async def get_available_services():
        """Get available services from TextVerified API."""
        logger.info(f"🔔 NOTIFICATION SYSTEM VERSION: {NOTIFICATION_SYSTEM_VERSION}")
        try:

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
        raise HTTPException(status_code=500, detail="Failed to fetch services from TextVerified API")


        @router.post("/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
    async def create_verification(
        verification_data: VerificationCreate,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Create new SMS verification."""
        try:
        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        # Check for duplicate request (idempotency)
        if verification_data.idempotency_key:
            existing = (
                db.query(Verification)
                .filter(
                    Verification.user_id == user_id,
                    Verification.idempotency_key == verification_data.idempotency_key,
                    Verification.created_at > datetime.now(timezone.utc) - timedelta(minutes=5),
                )
                .first()
            )
        if existing:
                logger.info(f"Returning cached verification for idempotency key: {verification_data.idempotency_key}")
        return {
                    "id": existing.id,
                    "service_name": existing.service_name,
                    "phone_number": existing.phone_number,
                    "capability": existing.capability,
                    "status": existing.status,
                    "cost": existing.cost,
                    "created_at": existing.created_at.isoformat(),
                    "completed_at": None,
                    "fallback_applied": False,
                }

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        base_cost = 0.50

        if current_user.free_verifications > 0:
            # Free verifications don't support custom filters normally
        if verification_data.area_code or verification_data.carrier:
        if current_user.credits < 1.0:  # Buffer for premium features
                    raise HTTPException(
                        status_code=402,
                        detail="Premium filters require credits even for free users",
                    )
            current_user.free_verifications -= 1
            db.commit()
        elif current_user.credits >= base_cost:
            old_balance = current_user.credits
            current_user.credits -= base_cost

            # Create transaction record
        try:

                transaction = Transaction(
                    user_id=user_id,
                    amount=-base_cost,
                    type="sms_purchase",
                    description=f"{verification_data.service_name} verification ({verification_data.country})",
                    service=verification_data.service_name,
                    status="completed",
                )
                db.add(transaction)

                # Send deduction notification using dispatcher
                dispatcher = NotificationDispatcher(db)
                dispatcher.on_credit_deducted(user_id, base_cost, verification_data.service_name)

                logger.critical(
                    f"🔔 NOTIFICATION SYSTEM ACTIVE - Transaction created: User={user_id}, Amount=-${base_cost}, Balance: ${old_balance:.2f} → ${current_user.credits:.2f}"
                )
        except Exception as notif_error:
                logger.error(f"Failed to create transaction/notification: {notif_error}")
                # Don't fail the verification, just log

            db.commit()
        else:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        # Tier-based feature gating
        tier_manager = TierManager(db)
        if verification_data.area_code and verification_data.area_code != "any":
        if not tier_manager.check_feature_access(user_id, "area_code_selection"):
                user_tier = tier_manager.get_user_tier(user_id)
                raise_tier_error(user_tier, "payg", user_id)

        if verification_data.carrier and verification_data.carrier != "any":
        if not tier_manager.check_feature_access(user_id, "isp_filtering"):
                user_tier = tier_manager.get_user_tier(user_id)
                raise_tier_error(user_tier, "pro", user_id)

        # Get TextVerified service

        tv_service = TextVerifiedService()

        if not tv_service.enabled:
            raise HTTPException(status_code=503, detail="SMS service unavailable")

        # Purchase number from TextVerified with optional filters
        fallback_applied = False
        try:
            result = await tv_service.create_verification(
                service=verification_data.service_name,
                country=verification_data.country,
                area_code=verification_data.area_code,
                carrier=verification_data.carrier,
            )
        except Exception as e:
            # Task 10: Intelligent Fallback (Tier 4 Turbo)
            user_tier = tier_manager.get_user_tier(user_id)
            is_turbo = user_tier in [
                "turbo",
                "custom",
            ]  # Assuming 'turbo' or 'custom' are Tier 4

            # Check if failure is likely due to filters (area code/carrier)
            has_filters = verification_data.area_code or verification_data.carrier

        if is_turbo and has_filters:
                logger.warning(f"Verification failed with filters for user {user_id}. Attempting fallback. Error: {e}")
        try:
                    # Retry without filters
                    result = await tv_service.create_verification(
                        service=verification_data.service_name,
                        country=verification_data.country,
                        area_code=None,
                        carrier=None,
                    )
                    fallback_applied = True
        except Exception as fallback_error:
                    logger.error(f"Fallback verification also failed: {fallback_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Verification failed even after fallback: {str(fallback_error)}",
                    )
        else:
                raise e

        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=verification_data.capability,
            status="pending",
            cost=result["cost"],
            phone_number=result["phone_number"],
            country=verification_data.country,
            activation_id=result["id"],
            provider="textverified",
            requested_area_code=verification_data.area_code,
            requested_carrier=verification_data.carrier,
            idempotency_key=verification_data.idempotency_key,
        )

        db.add(verification)
        db.commit()
        db.refresh(verification)

        logger.info(f"Verification created: {verification.id}")

        # Send verification created notification using dispatcher
        try:

            dispatcher = NotificationDispatcher(db)
            dispatcher.on_verification_created(verification)
        except Exception as notif_error:
            logger.error(f"Failed to dispatch verification created notification: {notif_error}")
        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at.isoformat(),
            "completed_at": None,
            "fallback_applied": fallback_applied,
            "carrier": verification.requested_carrier,
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
        verification = db.query(Verification).filter(Verification.id == verification_id).first()

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
            "completed_at": (verification.completed_at.isoformat() if verification.completed_at else None),
        }
        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Status fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch verification status")


        @router.get("/history", response_model=VerificationHistoryResponse)
    def get_verification_history(

        limit: int = 50,
        offset: int = 0,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Get verification history."""
        try:
        logger.info(f"Fetching verification history for user {user_id}, limit={limit}, offset={offset}")

        query = db.query(Verification).filter(Verification.user_id == user_id)

        # Get total count before pagination
        total_count = query.count()
        logger.info(f"Total verifications for user {user_id}: {total_count}")

        # Apply pagination and sorting
        verifications = query.order_by(Verification.created_at.desc()).offset(offset).limit(limit).all()
        logger.info(f"Retrieved {len(verifications)} verifications after pagination")

        response_list = []
        for v in verifications:
            response_list.append(
                VerificationResponse(
                    id=v.id,
                    service_name=v.service_name,
                    phone_number=v.phone_number,
                    capability=v.capability,
                    status=v.status,
                    cost=v.cost,
                    created_at=v.created_at.isoformat(),
                    completed_at=v.completed_at.isoformat() if v.completed_at else None,
                    fallback_applied=False,  # We might want to store this in DB if possible
                    sms_code=v.sms_code,
                    sms_text=v.sms_text,
                    carrier=v.requested_carrier or v.operator,
                )
            )

        logger.info(f"Successfully built response with {len(response_list)} items")
        return VerificationHistoryResponse(
            verifications=response_list,
            total_count=total_count,
        )
        except Exception as e:
        logger.error(f"History fetch error for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch verification history")


        @router.get("/{verification_id}/status")
    async def get_verification_status_polling(
        verification_id: str,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Get verification status for polling."""
        try:
        verification = (
            db.query(Verification).filter(Verification.id == verification_id, Verification.user_id == user_id).first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Check if SMS received via TextVerified
        if verification.status == "pending" and verification.activation_id:

            tv_service = TextVerifiedService()

        try:
                sms_result = await tv_service.get_sms(verification.activation_id)
        if sms_result and sms_result.get("sms_code"):
                    verification.sms_code = sms_result["sms_code"]
                    verification.sms_text = sms_result.get("sms_text", "")
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(f"SMS received for verification {verification_id}: {sms_result['sms_code']}")

                    # Send SMS received notification
        try:
                            NotificationService,
                        )

                        notif_service = NotificationService(db)
                        notif_service.create_notification(
                            user_id=verification.user_id,
                            notification_type="sms_received",
                            title="✅ SMS Code Received",
                            message=f"Code: {sms_result['sms_code']} for {verification.service_name}",
                        )
                        db.commit()
        except Exception as notif_error:
                        logger.error(f"Failed to send SMS received notification: {notif_error}")
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
            "completed_at": (verification.completed_at.isoformat() if verification.completed_at else None),
        }
        except HTTPException:
        raise
        except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check verification status")


        @router.delete("/{verification_id}", response_model=SuccessResponse)
    async def cancel_verification(
        verification_id: str,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Cancel verification and release number."""
        try:
        verification = (
            db.query(Verification).filter(Verification.id == verification_id, Verification.user_id == user_id).first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Release number via TextVerified if still active
        if verification.activation_id and verification.status == "pending":
        try:

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