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
from app.models.carrier_analytics import CarrierAnalytics
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationRequest
from app.services.balance_service import BalanceService
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_service import NotificationService
from app.services.pricing_calculator import PricingCalculator
from app.services.sms_polling_service import sms_polling_service
from app.services.textverified_service import TextVerifiedService
from app.services.tier_manager import TierManager
from app.services.transaction_service import TransactionService
from app.core.exceptions import AreaCodeUnavailableException
from fastapi.responses import JSONResponse

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

        # TIER VALIDATION: Check tier access for filtering features
        # Uses TierManager which refreshes from DB to avoid stale tier data
        tier_manager = TierManager(db)
        user_tier = tier_manager.get_user_tier(user_id)
        logger.info(f"Tier check for user {user_id}: resolved tier = {user_tier}")

        area_code = request.area_codes[0] if request.area_codes else None
        city = request.city

        # VOICE TIER GATE
        if request.capability == "voice":
            if not tier_manager.check_tier_hierarchy(user_tier, "payg"):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Voice verification requires PAYG tier or higher. Upgrade your plan.",
                )

        if request.area_codes:
            if not tier_manager.check_feature_access(user_id, "area_code_selection"):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Area code filtering requires PAYG tier or higher. Upgrade your plan.",
                )

        # CITY TIER GATE
        if city and request.country.upper() != "US":
            if not tier_manager.check_feature_access(user_id, "city_filtering"):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="City filtering requires PAYG tier or higher. Upgrade your plan.",
                )

        # Calculate SMS cost using new pricing system
        # Get pricing for this SMS
        filters = {"area_code": area_code, "city": city} if area_code or city else None
        pricing_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)
        sms_cost = pricing_info["total_cost"]

        logger.info(f"User {user_id} tier: {user_tier}, SMS cost: ${sms_cost:.2f}")

        # Check user has sufficient balance using unified service
        balance_check = await BalanceService.check_sufficient_balance(
            user_id, sms_cost, db
        )

        if not balance_check["sufficient"]:
            logger.warning(
                f"User {user_id} insufficient balance: "
                f"${balance_check['current_balance']:.2f} < ${sms_cost:.2f} "
                f"(source: {balance_check['source']})"
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Insufficient balance. "
                    f"Available: ${balance_check['current_balance']:.2f}, "
                    f"Required: ${sms_cost:.2f}"
                ),
            )

        old_balance = balance_check["current_balance"]

        logger.info(
            f"Purchasing number for service='{request.service}', country='{request.country}', user={user_id}"
        )

        area_code = request.area_codes[0] if request.area_codes else None
        carrier = getattr(request, "carrier", None)
        city = request.city

        if area_code:
            logger.info(f"User {user_id} requesting area code: {area_code}")
        if city:
            logger.info(f"User {user_id} requesting city: {city}")

        textverified_result = None
        verification = None
        notification_dispatcher = NotificationDispatcher(db)

        try:
            # Purchase via TextVerified
            logger.info(
                f"Calling TextVerified - Service: {request.service}, Country: {request.country}, Area Code: {area_code}"
            )
            textverified_result = await tv_service.create_verification(
                service=request.service,
                country=request.country,
                area_code=area_code,
                capability=request.capability,
                selected_from_alternatives=request.selected_from_alternatives,
                original_request=request.original_request,
            )
            provider_name = "textverified"
        except AreaCodeUnavailableException as area_err:
            # Area code is confirmed unavailable — no credits were charged (number was cancelled)
            db.rollback()
            logger.warning(
                f"Area code unavailable for user {user_id}: {area_err.message}"
            )
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "area_code_unavailable",
                    "message": area_err.message,
                    "alternatives": area_err.alternatives,
                    "credits_charged": False,
                }
            )

        # —— Success path: textverified_result is populated ——
        logger.info(
            f"TextVerified success: {textverified_result['phone_number']}, id: {textverified_result['id']}"
        )

        if textverified_result.get("fallback_applied"):
            logger.warning(
                f"Area code fallback for user {user_id}: "
                f"requested={textverified_result['requested_area_code']}, "
                f"assigned={textverified_result['assigned_area_code']}"
            )
            try:
                await notification_dispatcher.notify_area_code_fallback(
                    user_id=user_id,
                    verification_id="pending",
                    service=request.service,
                    requested_area_code=textverified_result["requested_area_code"],
                    assigned_area_code=textverified_result["assigned_area_code"],
                    same_state=textverified_result.get("same_state_fallback", True),
                )
            except Exception:
                pass  # Notification failure is non-fatal

        # Step 2.2: Create verification record
        actual_cost = sms_cost
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
            requested_area_code=area_code,
            requested_carrier=None,
            operator=None,
            assigned_area_code=textverified_result.get("assigned_area_code"),
            assigned_carrier=None,
            fallback_applied=textverified_result.get("fallback_applied", False),
            same_state_fallback=textverified_result.get("same_state_fallback", True),
            retry_attempts=textverified_result.get("attempt_count", 1),
            area_code_matched=textverified_result.get("area_code_matched", True),
            carrier_matched=True,       # carrier feature retired
            real_carrier=None,          # carrier feature retired
            carrier_surcharge=pricing_info.get("carrier_surcharge", 0.0),
            area_code_surcharge=pricing_info.get("area_code_surcharge", 0.0),
            voip_rejected=textverified_result.get("voip_rejected", False),
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification)
        db.flush()  # Get the ID before commit

        # Step 2.3: Process automatic refunds
        refund_service = RefundService()
        refund_result = await refund_service.process_refund(verification, user, db)

        if refund_result["refund_issued"]:
            logger.info(
                f"Refund issued: user={user_id}, amount=${refund_result['refund_amount']:.2f}, "
                f"type={refund_result['refund_type']}, reason={refund_result['reason']}"
            )
            actual_cost -= refund_result["refund_amount"]
            verification.cost = type(verification.cost)(actual_cost)

        logger.info(f"Verification record created with ID: {verification.id}")

        # Step 3: Deduct credits and record transaction
        # For admin users, sync from live TextVerified balance
        if user.is_admin:
            try:
                tv_bal = await tv_service.get_balance()
                new_balance = tv_bal.get("balance", 0.0)
                user.credits = new_balance
                logger.info(
                    f"Admin balance synced after purchase: ${old_balance:.2f} → ${new_balance:.2f}"
                )
            except Exception as sync_err:
                logger.warning(f"Post-purchase balance sync failed: {sync_err}")
                new_balance = old_balance - actual_cost
                user.credits = new_balance
        else:
            user.credits -= type(user.credits)(actual_cost)
            new_balance = float(user.credits)
            logger.info(
                f"User balance deducted: ${old_balance:.2f} → ${new_balance:.2f}"
            )

        # Record transaction
        TransactionService.record_sms_purchase(
            db=db,
            user_id=user_id,
            amount=actual_cost,
            service=request.service,
            verification_id=str(verification.id),
            old_balance=old_balance,
            new_balance=new_balance,
            filters={"area_code": area_code} if area_code else None,
            tier=user_tier,
        )

        # Notify user of credit deduction
        try:
            await notification_dispatcher.notify_verification_started(
                user_id=user_id,
                verification_id=str(verification.id),
                service=request.service,
                phone_number=textverified_result["phone_number"],
                cost=actual_cost,
            )
        except (TypeError, AttributeError) as e:
            logger.warning(f"Failed to send verification notification: {e}")

        except HTTPException:
            raise
        except Exception as api_error:
            db.rollback()

            logger.error(
                f"Purchase failed, transaction rolled back: {str(api_error)}",
                exc_info=True,
            )

            if textverified_result and textverified_result.get("id"):
                try:
                    await tv_service.cancel_verification(textverified_result["id"])
                except Exception as cancel_error:
                    logger.error(
                        f"Failed to cancel number after rollback: {cancel_error}"
                    )

            try:
                await notification_dispatcher.notify_verification_failed(
                    user_id=user_id,
                    verification_id="unknown",
                    service=request.service,
                    reason="Verification service temporarily unavailable",
                )
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Verification is temporarily unavailable. Your credits were not charged.",
            )

        # Record usage for quota tracking
        QuotaService.add_quota_usage(db, user_id, actual_cost)

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

        # Notification: Balance Updated — send before commit so created_at is
        # ordered after verification_started (same transaction window)
        try:
            await notification_dispatcher.notify_balance_deducted(
                user_id=user_id,
                amount=actual_cost,
                service=request.service,
                new_balance=float(new_balance),
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
            "fallback_applied": textverified_result.get("fallback_applied", False),
            "requested_area_code": textverified_result.get("requested_area_code"),
            "assigned_area_code": textverified_result.get("assigned_area_code"),
            "same_state_fallback": textverified_result.get("same_state_fallback", True),
            "requested_city": city,
            "city_honoured": textverified_result.get("city_honoured", True),
            "city_note": textverified_result.get("city_note"),
        }

        # Cache response for idempotency (24 hours)
        if final_idempotency_key:
            try:
                redis = get_redis()
                cache_key = f"idempotency:{user_id}:{final_idempotency_key}"
                redis.setex(cache_key, 86400, json.dumps(response))
            except Exception as cache_error:
                logger.warning(f"Failed to cache response: {cache_error}")

        logger.info(
            f"✓ Verification {verification.id} completed successfully | "
            f"User: {user_id} | Service: {request.service} | Country: {request.country} | "
            f"Phone: {textverified_result['phone_number']} | Cost: ${actual_cost:.2f} | "
            f"Balance: ${new_balance:.2f}"
        )

        try:

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
            detail="Invalid request. Please check your inputs and try again.",
        )
    except ConnectionError as e:
        db.rollback()
        logger.error(f"SMS provider connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification service is temporarily unavailable. Please try again.",
        )
    except TimeoutError as e:
        db.rollback()
        logger.error(f"Timeout in verification request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Verification is taking longer than expected. Please try again.",
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
        try:
            db.close()
        except Exception as close_err:
            logger.error(f"Error closing database session: {close_err}")


# Import for test mocking - must be at end to avoid circular imports
from app.services.quota_service import QuotaService  # noqa: E402
from app.services.refund_service import RefundService  # noqa: E402
