"""SMS verification purchase endpoints."""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.cache import get_redis
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.exceptions import AreaCodeUnavailableException
from app.core.logging import get_logger
from app.models.carrier_analytics import CarrierAnalytics
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationRequest
from app.services.balance_service import BalanceService
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_service import NotificationService
from app.services.pricing_calculator import PricingCalculator
from app.services.purchase_intelligence import PurchaseIntelligenceService
from app.services.sms_polling_service import sms_polling_service
from app.services.textverified_service import TextVerifiedService
from app.services.tier_manager import TierManager
from app.services.transaction_service import TransactionService

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

        # Provider Router Initialization
        from app.services.providers.provider_router import ProviderRouter

        provider_router = ProviderRouter()

        enabled_providers = provider_router.get_enabled_providers()
        if not enabled_providers:
            logger.error("No SMS providers configured or available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service temporarily unavailable. Please try again later.",
            )
        logger.info(f"Multi-provider router initialized. Enabled: {enabled_providers}")

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

        purchase_result = None
        verification = None
        notification_dispatcher = NotificationDispatcher(db)

        try:
            try:
                # Purchase via Router (Multi-provider with Failover)
                logger.info(
                    f"Initiating purchase through ProviderRouter - Service: {request.service}, Country: {request.country}"
                )
                purchase_result = await provider_router.purchase_with_failover(
                    db=db,
                    service=request.service,
                    country=request.country,
                    area_code=area_code,
                    capability=request.capability,
                    city=city,
                    user_tier=user_tier,
                    selected_from_alternatives=request.selected_from_alternatives,
                    original_request=request.original_request,
                )
                provider_name = purchase_result.provider
            except AreaCodeUnavailableException as area_err:
                # Area code is confirmed unavailable — handled by TextVerified path within router
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
                    },
                )

            # —— Success path: purchase_result is populated ——
            if purchase_result.fallback_applied:
                logger.warning(
                    f"Provider fallback applied for user {user_id}: "
                    f"requested={purchase_result.requested_area_code or 'Any'}, "
                    f"assigned={purchase_result.assigned_area_code or 'Any'}"
                )
                try:
                    await notification_dispatcher.notify_area_code_fallback(
                        user_id=user_id,
                        verification_id="pending",
                        service=request.service,
                        requested_area_code=purchase_result.requested_area_code,
                        assigned_area_code=purchase_result.assigned_area_code,
                        same_state=purchase_result.same_state_fallback,
                    )
                except Exception:
                    pass  # Notification failure is non-fatal

            # Step 2.2: Create verification record
            actual_cost = sms_cost
            logger.info(f"Creating verification record for user {user_id}")
            verification = Verification(
                user_id=user_id,
                service_name=request.service,
                phone_number=purchase_result.phone_number,
                country=request.country,
                capability=request.capability,
                cost=actual_cost,
                provider=purchase_result.provider,
                activation_id=purchase_result.order_id,
                status="pending",
                idempotency_key=final_idempotency_key,
                requested_area_code=area_code,
                requested_carrier=None,
                operator=purchase_result.operator,
                assigned_area_code=purchase_result.assigned_area_code,
                assigned_carrier=None,
                fallback_applied=purchase_result.fallback_applied,
                same_state_fallback=purchase_result.same_state_fallback,
                retry_attempts=purchase_result.retry_attempts,
                area_code_matched=purchase_result.area_code_matched,
                carrier_matched=True,  # carrier feature retired
                real_carrier=None,  # carrier feature retired
                carrier_surcharge=pricing_info.get("carrier_surcharge", 0.0),
                area_code_surcharge=pricing_info.get("area_code_surcharge", 0.0),
                voip_rejected=purchase_result.voip_rejected,
                created_at=datetime.now(timezone.utc),
                selected_from_alternatives=request.selected_from_alternatives,
                original_request=request.original_request,
                routing_reason=purchase_result.routing_reason,
                city_honoured=purchase_result.city_honoured,
                city_note=purchase_result.city_note,
            )
            db.add(verification)
            db.flush()  # Get the ID before commit

            # --- INSTITUTIONAL TELEMETRY ---
            # Fire-and-forget logging to Purchase Intelligence
            asyncio.create_task(
                PurchaseIntelligenceService.log_outcome(
                    service=request.service,
                    assigned_code=purchase_result.assigned_area_code or "",
                    requested_code=area_code,
                    matched=purchase_result.area_code_matched if area_code else True,
                    user_id=user_id,
                    verification_id=str(verification.id),
                    provider=purchase_result.provider,
                    country=request.country,
                    provider_cost=purchase_result.cost,
                    user_price=actual_cost,
                )
            )

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
            # For admin users, sync from live provider balance if available
            if user.is_admin:
                try:
                    balances = await provider_router.get_provider_balances()
                    new_balance = balances.get(
                        purchase_result.provider, old_balance - actual_cost
                    )
                    user.credits = new_balance
                    logger.info(
                        f"Admin balance synced after purchase: ${old_balance:.2f} → ${new_balance:.2f}"
                    )
                except Exception as sync_err:
                    logger.warning(f"Post-purchase balance sync failed: {sync_err}")
                    new_balance = old_balance - actual_cost
                    user.credits = new_balance
            else:
                # Use unified deduction service (Phase 2.4/5)
                success, error = BalanceService.deduct_credits_for_verification(
                    db=db,
                    user=user,
                    verification=verification,
                    cost=actual_cost,
                    service_name=request.service,
                    country_code=request.country,
                )

                if not success:
                    # Error handling handled within service (verification marked failed)
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=error or "Credit deduction failed",
                    )

                new_balance = float(user.credits)

            # Notify user of credit deduction
            try:
                await notification_dispatcher.notify_verification_started(
                    user_id=user_id,
                    verification_id=str(verification.id),
                    service=request.service,
                    phone_number=purchase_result.phone_number,
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

            if purchase_result and purchase_result.order_id:
                try:
                    # Attempt cancellation on provider side
                    from app.services.providers.textverified_adapter import (
                        TextVerifiedAdapter,
                    )

                    if purchase_result.provider == "textverified":
                        await TextVerifiedAdapter().cancel(purchase_result.order_id)
                    # Add other providers if they support explicit cancel
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

        # Notification: Balance Updated
        try:
            await notification_dispatcher.notify_balance_deducted(
                user_id=user_id,
                amount=actual_cost,
                service=request.service,
                new_balance=float(new_balance),
            )
        except Exception:
            pass

        # CRITICAL: Commit transaction
        db.commit()
        logger.info(
            f"Transaction committed successfully for verification {verification.id}"
        )

        # Build response
        response = {
            "success": True,
            "verification_id": verification.id,
            "phone_number": purchase_result.phone_number,
            "service": request.service,
            "country": request.country,
            "cost": actual_cost,
            "status": "pending",
            "activation_id": purchase_result.order_id,
            "demo_mode": False,
            "fallback_applied": purchase_result.fallback_applied,
            "requested_area_code": purchase_result.requested_area_code,
            "assigned_area_code": purchase_result.assigned_area_code,
            "same_state_fallback": purchase_result.same_state_fallback,
            "requested_city": city,
            "city_honoured": purchase_result.city_honoured,
            "city_note": purchase_result.city_note,
            "provider": purchase_result.provider,
            "routing_reason": purchase_result.routing_reason,
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
            f"Phone: {purchase_result.phone_number} | Cost: ${actual_cost:.2f} | "
            f"Balance: ${new_balance:.2f} | Provider: {purchase_result.provider}"
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
