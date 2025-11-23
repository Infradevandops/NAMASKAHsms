"""Enhanced SMS Verification API with comprehensive error handling."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])


@router.post("/create",
             response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification with enhanced error handling."""
    try:
        logger.info(f"Creating verification for user {user_id}")

        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        provider = provider_manager.get_primary_provider()
        if not provider:
            logger.error("No SMS provider available")
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again later."
            )

        country = getattr(verification_data, "country", "US")

        # Check provider balance
        try:
            balance_data = await provider.get_balance()
            balance = balance_data.get("balance", 0.0)
            if balance < 0.50:
                logger.warning(f"Provider balance low: ${balance}")
                raise HTTPException(
                    status_code=503,
                    detail="SMS provider balance insufficient. Please contact support."
                )
        except HTTPException:
        pass
        except Exception as e:
            logger.error(f"Provider balance check failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Unable to verify SMS provider status. Please try again."
            )

        base_cost = 0.50
        final_cost = base_cost

        # Check user credits
        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0.0
            db.commit()
        elif current_user.credits >= final_cost:
            current_user.credits -= final_cost
            actual_cost = final_cost
            db.commit()
        else:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need ${final_cost:.2f}, have ${current_user.credits:.2f}"
            )

        # Purchase number
        try:
            number_data = await provider.buy_number(country=country, service=verification_data.service_name)
            phone_number = number_data["phone_number"]
            activation_id = str(number_data["activation_id"])

            if "cost" in number_data:
                final_cost = number_data["cost"]

        except Exception as e:
            # Refund on failure
            if actual_cost > 0:
                current_user.credits += actual_cost
            else:
                current_user.free_verifications += 1
            db.commit()

            logger.error(f"Provider purchase failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Failed to purchase SMS number. Please try again."
            )

        # Create verification record
        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=getattr(verification_data, "capability", "sms"),
            status="pending",
            cost=actual_cost,
            phone_number=phone_number,
            country=country,
            verification_code=activation_id,
        )

        if hasattr(verification, 'provider'):
            verification.provider = "textverified"
        if hasattr(verification, 'activation_id'):
            verification.activation_id = activation_id

        db.add(verification)
        db.commit()
        db.refresh(verification)

        logger.info(f"Verification {verification.id} created successfully")

        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at,
            "completed_at": verification.completed_at
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Verification creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create verification")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get verification status with error handling."""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Check for SMS updates
        if verification.status == "pending" and verification.verification_code:
            try:
                provider = provider_manager.get_primary_provider()
                if provider:
                    sms_code = await provider.get_sms(verification.verification_code)
                    if sms_code:
                        verification.status = "completed"
                        verification.completed_at = datetime.now(timezone.utc)
                        if hasattr(verification, 'sms_code'):
                            verification.sms_code = sms_code
                        db.commit()
                        logger.info(f"SMS received for {verification_id}")
            except Exception as e:
                logger.error(f"SMS check failed: {str(e)}")

        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "created_at": verification.created_at.isoformat(),
            "provider": getattr(verification, "provider", "textverified"),
            "country": getattr(verification, "country", "US"),
            "completed_at": verification.completed_at.isoformat() if verification.completed_at else None
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve verification status")


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits."""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id,
            Verification.user_id == user_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        if verification.status in ["cancelled", "completed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel {verification.status} verification"
            )

        # Cancel on provider
        if verification.verification_code:
            try:
                provider = provider_manager.get_primary_provider()
                if provider:
                    await provider.cancel_activation(verification.verification_code)
            except Exception as e:
                logger.warning(f"Provider cancel failed: {str(e)}")

        # Refund credits
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        if verification.cost > 0:
            current_user.credits += verification.cost
        else:
            current_user.free_verifications += 1

        verification.status = "cancelled"
        db.commit()

        logger.info(f"Verification {verification_id} cancelled by user {user_id}")

        return SuccessResponse(
            message="Verification cancelled and refunded",
            data={"refunded": verification.cost, "new_balance": current_user.credits},
        )

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Cancel failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel verification")


@router.get("/{verification_id}/messages")
async def get_verification_messages(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get SMS messages for verification."""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        if not verification.verification_code:
            return {
                "messages": [],
                "status": verification.status,
                "verification_id": verification_id,
                "error": "No activation ID found"
            }

        try:
            provider = provider_manager.get_primary_provider()
            if not provider:
                raise Exception("Provider not available")

            sms_code = await provider.get_sms(verification.verification_code)
            messages = []

            if sms_code:
                messages.append({
                    "text": f"Your verification code is: {sms_code}",
                    "code": sms_code,
                    "date": datetime.now(timezone.utc).isoformat()
                })

                if verification.status == "pending":
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)
                    if hasattr(verification, 'sms_code'):
                        verification.sms_code = sms_code
                    db.commit()

            return {
                "messages": messages,
                "status": verification.status,
                "verification_id": verification_id,
                "code": sms_code,
                "phone": verification.phone_number,
                "provider": "textverified"
            }

        except Exception as e:
            logger.error(f"Message retrieval failed: {str(e)}")
            return {
                "messages": [],
                "status": verification.status,
                "verification_id": verification_id,
                "error": "Failed to retrieve messages"
            }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Message endpoint failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")
