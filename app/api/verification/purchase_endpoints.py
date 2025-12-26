"""SMS verification purchase endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import asyncio
import uuid
import random

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService
from app.services.notification_service import NotificationService
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationRequest

logger = get_logger(__name__)
router = APIRouter(prefix="/api/verification", tags=["Verification"])

# Required authentication dependency
from app.core.dependencies import get_current_user_id


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_verification(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service name is required"
        )
    
    if not request.country or len(request.country.strip()) == 0:
        logger.warning("Empty country code provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country code is required"
        )
    
    # Real verification with authentication required
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get TextVerified service
        logger.info(f"Initializing TextVerified service for user {user_id}")
        tv_service = TextVerifiedService()
        if not tv_service.enabled:
            logger.error("TextVerified service not configured or unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service temporarily unavailable. Please try again later."
            )
        logger.info("TextVerified service initialized successfully")
        
        # Calculate SMS cost using new pricing system
        from app.services.pricing_calculator import PricingCalculator
        
        calculator = PricingCalculator(db)
        user_tier = getattr(user, 'tier_id', 'payg') or 'payg'
        
        # Get pricing for this SMS
        pricing_info = calculator.calculate_sms_cost(user_id, user_tier)
        sms_cost = pricing_info["cost_per_sms"]
        
        logger.info(f"User {user_id} tier: {user_tier}, SMS cost: ${sms_cost:.2f}, within quota: {pricing_info['within_quota']}")
        
        # Check user has sufficient credits
        logger.info(f"User {user_id} current balance: ${user.credits:.2f}, SMS cost: ${sms_cost:.2f}")
        if user.credits < sms_cost:
            logger.warning(f"User {user_id} has insufficient credits: ${user.credits:.2f} < ${sms_cost:.2f}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Available: ${user.credits:.2f}, Required: ${sms_cost:.2f}"
            )
        
        # Purchase number from TextVerified
        logger.info(f"Purchasing number for service='{request.service}', country='{request.country}', user={user_id}")
        result = await tv_service.buy_number(
            request.country,
            request.service
        )
        logger.info(f"Number purchased successfully: {result['phone_number']}, cost: ${result['cost']:.2f}")
        
        # Double-check credits after getting actual cost (use calculated cost, not TextVerified cost)
        actual_cost = sms_cost  # Use our pricing system cost
        if user.credits < actual_cost:
            logger.error(f"User {user_id} has insufficient credits: ${user.credits:.2f} < ${actual_cost:.2f}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: ${actual_cost:.2f}, Available: ${user.credits:.2f}"
            )
        
        # Create verification record
        logger.info(f"Creating verification record for user {user_id}")
        verification = Verification(
            user_id=user_id,
            service_name=request.service,
            phone_number=result["phone_number"],
            country=request.country,
            capability=request.capability,
            cost=actual_cost,  # Use our calculated cost
            provider="textverified",
            activation_id=result["activation_id"],
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db.add(verification)
        db.flush()  # Get the ID before commit
        logger.info(f"Verification record created with ID: {verification.id}")
        
        # Deduct credits from user (use our calculated cost)
        old_balance = user.credits
        user.credits -= actual_cost
        new_balance = user.credits
        logger.info(f"Deducting ${actual_cost:.2f} from user {user_id}: ${old_balance:.2f} → ${new_balance:.2f}")
        
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
                    message=f"Your balance is ${new_balance:.2f}. Add credits to continue."
                )
            except Exception:
                pass
        
        db.commit()
        logger.info(f"Transaction committed successfully for verification {verification.id}")
        
        # Notification: Verification Initiated
        try:
            notif_service = NotificationService(db)
            notif_service.create_notification(
                user_id=user_id,
                notification_type="verification_initiated",
                title="Verification Started",
                message=f"SMS verification for {request.service} initiated"
            )
        except Exception:
            pass
        
        logger.info(
            f"✓ Verification {verification.id} completed successfully | "
            f"User: {user_id} | Service: {request.service} | Country: {request.country} | "
            f"Phone: {result['phone_number']} | Cost: ${actual_cost:.2f} | "
            f"Balance: ${new_balance:.2f}"
        )
        
        try:
            from app.services.sms_polling_service import sms_polling_service
            asyncio.create_task(sms_polling_service.start_polling(verification.id))
            logger.info(f"Started SMS polling for verification {verification.id}")
        except Exception as poll_error:
            logger.warning(f"SMS polling start failed (non-critical): {poll_error}")
        
        return {
            "success": True,
            "verification_id": verification.id,
            "phone_number": result["phone_number"],
            "service": request.service,
            "country": request.country,
            "cost": actual_cost,
            "status": "pending",
            "activation_id": result["activation_id"],
            "demo_mode": False
        }
    
    except HTTPException as http_err:
        db.rollback()
        logger.warning(f"HTTP exception in verification request: {http_err.status_code} - {http_err.detail}")
        raise
    except ValueError as e:
        db.rollback()
        logger.warning(f"Validation error in verification request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except ConnectionError as e:
        db.rollback()
        logger.error(f"Connection error to TextVerified API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to SMS service. Please try again."
        )
    except TimeoutError as e:
        db.rollback()
        logger.error(f"Timeout error in verification request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout. Please try again."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in verification request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again or contact support."
        )
    finally:
        # Ensure database session is properly closed
        try:
            db.close()
        except Exception as close_err:
            logger.error(f"Error closing database session: {close_err}")
