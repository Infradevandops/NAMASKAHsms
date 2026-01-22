"""SMS verification purchase endpoints."""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import get_redis
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.middleware.tier_validation import validate_tier_access
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationRequest
from app.services.notification_service import NotificationService
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_verification(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    idempotency_key: str = Header(None, alias="X-Idempotency-Key"),
):
    """Request SMS verification - purchase phone number.

    Supports both authenticated users and demo mode.
    Demo mode: Returns simulated verification for testing.
    Authenticated mode: Uses TextVerified API and deducts credits.

    Rate Limiting: 10 requests per minute per user/IP
    """

    # Validate request
    if not request.service or len(request.service.strip()) == 0:
        logger.warning("Empty service name provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Service name is required"
        )

    if not request.country or len(request.country.strip()) == 0:
        logger.warning("Empty country code provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Country code is required"
        )

    # SAFETY: Check for duplicate request using idempotency key from header or request body
    final_idempotency_key = idempotency_key or request.idempotency_key
    if final_idempotency_key:
        # Check Redis cache first for fast response
        try:
            redis = get_redis()
            cache_key = f"idempotency:{user_id}:{final_idempotency_key}"
            cached_response = redis.get(cache_key)
            if cached_response:
                logger.info(
                    f"Returning cached response for idempotency key: {final_idempotency_key}"
                )
                return json.loads(cached_response)
        except Exception as cache_error:
            logger.warning(f"Redis cache check failed: {cache_error}")

        # Check database for existing verification
        existing = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id,
                Verification.idempotency_key == final_idempotency_key,
            )
            .first()
        )
        if existing:
            logger.info(f"Duplicate request detected: {final_idempotency_key}")
            response = {
                "success": True,
                "verification_id": existing.id,
                "phone_number": existing.phone_number,
                "service": existing.service_name,
                "country": existing.country,
                "cost": existing.cost,
                "status": existing.status,
                "activation_id": existing.activation_id,
                "demo_mode": False,
                "duplicate": True,
            }
            # Cache for 24 hours
            try:
                redis.setex(cache_key, 86400, json.dumps(response))
            except Exception:
                pass
            return response

    # Real verification with authentication required
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # TIER VALIDATION: Check tier access for carrier and area code selection
        area_code = request.area_codes[0] if request.area_codes else None
        carrier = request.carriers[0] if request.carriers else None
        validate_tier_access(user, carrier=carrier, area_code=area_code)

        # Get TextVerified service
        logger.info(f"Initializing TextVerified service for user {user_id}")
        tv_service = TextVerifiedService()
        if not tv_service.enabled:
            logger.error("TextVerified service not configured or unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service temporarily unavailable. Please try again later.",
            )
        logger.info("TextVerified service initialized successfully")

        # Check tier access for filtering features
        from app.services.tier_manager import TierManager

        tier_manager = TierManager(db)

        if request.area_codes:
            if not tier_manager.check_feature_access(user_id, "area_code_selection"):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Area code filtering requires payg tier or higher. Upgrade your plan.",
                )

        if request.carriers:
            if not tier_manager.check_feature_access(user_id, "isp_filtering"):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Carrier filtering requires payg tier or higher. Upgrade your plan.",
                )

        # Calculate SMS cost using new pricing system
        from app.services.pricing_calculator import PricingCalculator

        calculator = PricingCalculator(db)
        user_tier = user.subscription_tier or "freemium"

        # Get pricing for this SMS
        pricing_info = calculator.calculate_sms_cost(user_id, user_tier)
        sms_cost = pricing_info["cost_per_sms"]

        logger.info(
            f"User {user_id} tier: {user_tier}, SMS cost: ${sms_cost:.2f}, within quota: {pricing_info['within_quota']}"
        )

        # Check user has sufficient credits BEFORE calling API
        logger.info(
            f"User {user_id} current balance: ${user.credits:.2f}, SMS cost: ${sms_cost:.2f}"
        )
        if user.credits < sms_cost:
            logger.warning(
                f"User {user_id} has insufficient credits: ${user.credits:.2f} < ${sms_cost:.2f}"
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Available: ${user.credits:.2f}, Required: ${sms_cost:.2f}",
            )

        # CRITICAL FIX: Call TextVerified API FIRST (before deducting credits)
        logger.info(
            f"Purchasing number for service='{request.service}', country='{request.country}', user={user_id}"
        )

        # Pass area codes and carriers if provided
        area_code = request.area_codes[0] if request.area_codes else None
        carrier = request.carriers[0] if request.carriers else None

        textverified_result = None
        verification = None

        try:
            # Step 1: Call TextVerified API FIRST
            textverified_result = await tv_service.create_verification(
                service=request.service, area_code=area_code, carrier=carrier
            )
            logger.info(
                f"TextVerified API success: {textverified_result['phone_number']}, id: {textverified_result['id']}"
            )

            # Step 2: Create verification record (not committed yet)
            actual_cost = sms_cost  # Use our pricing system cost
            logger.info(f"Creating verification record for user {user_id}")
            verification = Verification(
                user_id=user_id,
                service_name=request.service,
                phone_number=textverified_result["phone_number"],
                country=request.country,
                capability=request.capability,
                cost=actual_cost,
                provider="textverified",
                activation_id=textverified_result["id"],
                status="pending",
                idempotency_key=final_idempotency_key,
                created_at=datetime.now(timezone.utc),
            )
            db.add(verification)
            db.flush()  # Get the ID before commit
            logger.info(f"Verification record created with ID: {verification.id}")

            # Step 3: Deduct credits ONLY after API success
            old_balance = user.credits
            user.credits -= actual_cost
            new_balance = user.credits
            logger.info(
                f"Deducting ${actual_cost:.2f} from user {user_id}: ${old_balance:.2f} → ${new_balance:.2f}"
            )

        except Exception as api_error:
            # CRITICAL: Rollback if TextVerified API fails
            db.rollback()
            logger.error(
                f"TextVerified API failed, transaction rolled back: {str(api_error)}",
                exc_info=True,
            )

            # If we got a number but DB failed, cancel it
            if textverified_result and textverified_result.get("id"):
                try:
                    await tv_service.cancel_verification(textverified_result["id"])
                    logger.info(
                        f"Cancelled TextVerified number: {textverified_result['id']}"
                    )
                except Exception as cancel_error:
                    logger.error(
                        f"Failed to cancel TextVerified number: {cancel_error}"
                    )

            # Notification: Verification Failed (Task 1.3)
            try:
                notif_service = NotificationService(db)
                notif_service.create_notification(
                    user_id=user_id,
                    notification_type="verification_failed",
                    title="⚠️ Verification Failed",
                    message=f"SMS service temporarily unavailable for {request.service}. Your credits were not charged.",
                )
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service temporarily unavailable. Your credits were not charged.",
            )

        # Record usage for quota tracking
        calculator.record_sms_usage(user_id, actual_cost)

        # Low balance warning
        if new_balance < 5.0 and old_balance >= 5.0:
            try:
                notif_service = NotificationService(db)
                notif_service.create_notification(
                    user_id=user_id,
                    notification_type="low_balance",
                    title="Low Balance Warning",
                    message=f"Your balance is ${new_balance:.2f}. Add credits to continue.",
                )
            except Exception:
                pass

        # CRITICAL: Commit transaction (all or nothing)
        db.commit()
        logger.info(
            f"Transaction committed successfully for verification {verification.id}"
        )

        # Build response
        response = {
            "success": True,
            "verification_id": verification.id,
            "phone_number": textverified_result["phone_number"],
            "service": request.service,
            "country": request.country,
            "cost": actual_cost,
            "status": "pending",
            "activation_id": textverified_result["id"],
            "demo_mode": False,
        }

        # Cache response for idempotency (24 hours)
        if final_idempotency_key:
            try:
                redis = get_redis()
                cache_key = f"idempotency:{user_id}:{final_idempotency_key}"
                redis.setex(cache_key, 86400, json.dumps(response))
            except Exception as cache_error:
                logger.warning(f"Failed to cache response: {cache_error}")

        # Notification: Balance Updated (Task 2.5)
        try:
            notif_service = NotificationService(db)
            notif_service.create_notification(
                user_id=user_id,
                notification_type="balance_update",
                title="💳 Balance Updated",
                message=f"${actual_cost:.2f} charged for {request.service} - New balance: ${new_balance:.2f}",
            )
        except Exception:
            pass

        # Notification: Number Purchased (Task 2.2)
        try:
            notif_service = NotificationService(db)
            notif_service.create_notification(
                user_id=user_id,
                notification_type="number_purchased",
                title="📱 Number Purchased",
                message=f"Phone: {textverified_result['phone_number']} - Waiting for SMS code...",
            )
        except Exception:
            pass

        # Notification: Verification Initiated (Task 2.1 Enhanced)
        try:
            notif_service = NotificationService(db)
            notif_service.create_notification(
                user_id=user_id,
                notification_type="verification_initiated",
                title="🎯 Verification Started",
                message=f"Purchasing {request.service} number in {request.country} for ${actual_cost:.2f}",
            )
        except Exception:
            pass

        logger.info(
            f"✓ Verification {verification.id} completed successfully | "
            f"User: {user_id} | Service: {request.service} | Country: {request.country} | "
            f"Phone: {textverified_result['phone_number']} | Cost: ${actual_cost:.2f} | "
            f"Balance: ${new_balance:.2f}"
        )

        try:
            from app.services.sms_polling_service import sms_polling_service

            asyncio.create_task(sms_polling_service.start_polling(verification.id))
            logger.info(f"Started SMS polling for verification {verification.id}")
        except Exception as poll_error:
            logger.warning(f"SMS polling start failed (non-critical): {poll_error}")

        return response

    except HTTPException as http_err:
        db.rollback()
        logger.warning(
            f"HTTP exception in verification request: {http_err.status_code} - {http_err.detail}"
        )
        raise
    except ValueError as e:
        db.rollback()
        logger.warning(f"Validation error in verification request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except ConnectionError as e:
        db.rollback()
        logger.error(f"Connection error to TextVerified API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to SMS service. Please try again.",
        )
    except TimeoutError as e:
        db.rollback()
        logger.error(f"Timeout error in verification request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout. Please try again.",
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"Unexpected error in verification request: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again or contact support.",
        )
    finally:
        # Ensure database session is properly closed
        try:
            db.close()
        except Exception as close_err:
            logger.error(f"Error closing database session: {close_err}")
