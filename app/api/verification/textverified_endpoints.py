"""Real TextVerified verification endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import asyncio

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/verify", tags=["verification"])
integration = get_textverified_integration()


@router.post("/create")
async def create_verification(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create real SMS verification with TextVerified API."""
    try:
        data = await request.json()
        service = data.get("service")
        area_code = data.get("area_code")
        carrier = data.get("carrier")

        if not service:
            raise HTTPException(status_code=400, detail="Service required")

        # Get user and check balance
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get pricing
        cost = await integration.get_service_pricing(service)

        if user.credits < cost:
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # Create verification with real API
        result = await integration.create_verification(
            service=service, area_code=area_code, carrier=carrier
        )

        # Deduct cost from user balance
        user.credits -= cost
        db.commit()

        # Store verification in database
        verification = Verification(
            user_id=user_id,
            service_name=service,
            phone_number=result["phone_number"],
            status="pending",
            cost=cost,
            activation_id=result["id"],
        )
        db.add(verification)
        db.commit()

        # Start SMS polling in background
        asyncio.create_task(_poll_sms_background(verification.id, result["id"], db))

        return {
            "success": True,
            "id": verification.id,
            "activation_id": result["id"],
            "phone_number": result["phone_number"],
            "status": "pending",
            "cost": cost,
            "created_at": verification.created_at.isoformat(),
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Verification creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create verification")


@router.get("/{verification_id}/status")
async def get_verification_status(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get real verification status from TextVerified API."""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id, Verification.user_id == user_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Get status from TextVerified API
        status_data = await integration.get_verification_status(verification.activation_id)

        # Update local status
        verification.status = status_data.get("status", "pending")
        db.commit()

        # Get SMS codes if completed
        sms_codes = []
        if verification.status == "completed":
            sms_codes = await integration.get_sms_codes(verification.activation_id)

        return {
            "success": True,
            "id": verification.id,
            "status": verification.status,
            "phone_number": verification.phone_number,
            "sms_codes": sms_codes,
            "created_at": verification.created_at.isoformat(),
            "updated_at": verification.updated_at.isoformat(),
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Get verification status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verification status")


@router.get("/balance")
async def get_balance(user_id: str = Depends(get_current_user_id)):
    """Get real TextVerified account balance."""
    try:
        balance = await integration.get_account_balance()
        return {
            "success": True,
            "balance": balance,
            "currency": "USD",
        }
    except Exception as e:
        logger.error(f"Get balance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get balance")


@router.get("/services")
async def get_services():
    """Get real services from TextVerified API."""
    try:
        services = await integration.get_services_list()
        return {
            "success": True,
            "services": services,
            "total": len(services),
        }
    except Exception as e:
        logger.error(f"Get services error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get services")


@router.get("/area-codes")
async def get_area_codes():
    """Get real area codes from TextVerified API."""
    try:
        codes = await integration.get_area_codes_list()
        return {
            "success": True,
            "area_codes": codes,
            "total": len(codes),
        }
    except Exception as e:
        logger.error(f"Get area codes error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get area codes")


@router.delete("/{verification_id}")
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits."""
    try:
        verification = db.query(Verification).filter(
            Verification.id == verification_id, Verification.user_id == user_id
        ).first()

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Refund credits
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += verification.cost
            verification.status = "cancelled"
            db.commit()

        return {
            "success": True,
            "message": "Verification cancelled and refunded",
            "refund_amount": verification.cost,
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Cancel verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel verification")


async def _poll_sms_background(verification_id: str, activation_id: str, db: Session):
    """Background task to poll SMS codes."""
    max_attempts = 120  # 10 minutes
    attempt = 0

    while attempt < max_attempts:
        try:
            codes = await integration.get_sms_codes(activation_id)
            if codes:
                verification = db.query(Verification).filter(
                    Verification.id == verification_id
                ).first()
                if verification:
                    verification.status = "completed"
                    verification.sms_code = codes[0]
                    db.commit()
                    logger.info(f"SMS received for verification {verification_id}")
                    break
        except Exception as e:
            logger.debug(f"SMS polling error: {e}")

        attempt += 1
        await asyncio.sleep(5)  # Poll every 5 seconds
