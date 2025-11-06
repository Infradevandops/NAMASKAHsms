"""Simplified verification API without TextVerified dependency."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.schemas import (
    SuccessResponse,
    VerificationCreate,
    VerificationHistoryResponse,
    VerificationResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/services")
async def get_available_services():
    """Get available SMS verification services."""
    return {
        "services": [
            {"id": "1", "name": "Telegram", "price": 0.50},
            {"id": "2", "name": "WhatsApp", "price": 0.60},
            {"id": "3", "name": "Google", "price": 0.40},
            {"id": "4", "name": "Facebook", "price": 0.70},
            {"id": "5", "name": "Instagram", "price": 0.80},
            {"id": "6", "name": "Discord", "price": 0.50},
        ]
    }


@router.post(
    "/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED
)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create new SMS verification (demo mode)."""
    try:
        capability = getattr(verification_data, "capability", "sms")
        country = getattr(verification_data, "country", "US")

        if not verification_data.service_name:
            raise HTTPException(status_code=400, detail="Service name is required")

        # Get user and check credits
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        cost = 0.50  # Default cost

        # Check if user has sufficient credits or free verifications
        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0
        elif current_user.credits >= cost:
            current_user.credits -= cost
            actual_cost = cost
        else:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need ${cost:.2f}, have ${current_user.credits:.2f}",
            )

        # Create demo verification
        import random
        import uuid

        phone_number = f"+1555{random.randint(1000000, 9999999)}"
        number_id = str(uuid.uuid4())[:8]

        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=capability,
            status="pending",
            cost=actual_cost,
            phone_number=phone_number,
            country=country,
            verification_code=number_id,
        )

        db.add(verification)
        db.commit()
        db.refresh(verification)

        return {
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": verification.cost,
            "remaining_credits": current_user.credits,
            "created_at": verification.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Verification creation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status."""
    verification = (
        db.query(Verification).filter(Verification.id == verification_id).first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    return VerificationResponse.from_orm(verification)


@router.get("/{verification_id}/messages")
async def get_verification_messages(
    verification_id: str, db: Session = Depends(get_db)
):
    """Get SMS messages for verification (demo mode)."""
    try:
        verification = (
            db.query(Verification).filter(Verification.id == verification_id).first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        # Demo SMS code
        demo_code = "123456"

        # Update verification status
        verification.status = "completed"
        verification.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "messages": [{"text": demo_code}],
            "status": "completed",
            "verification_id": verification_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get messages for %s: %s", verification_id, str(e))
        return {
            "messages": [],
            "status": "error",
            "error": "Failed to retrieve messages",
        }


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None, description="Filter by service name"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Get user's verification history with filtering."""
    query = db.query(Verification).filter(Verification.user_id == user_id)

    if service:
        query = query.filter(Verification.service_name == service)
    if verification_status:
        query = query.filter(Verification.status == verification_status)

    total = query.count()
    verifications = (
        query.order_by(Verification.created_at.desc()).offset(skip).limit(limit).all()
    )

    return VerificationHistoryResponse(
        verifications=[VerificationResponse.from_orm(v) for v in verifications],
        total_count=total,
    )


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification and refund credits."""
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == user_id)
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    # Refund credits
    current_user = db.query(User).filter(User.id == user_id).first()
    current_user.credits += verification.cost

    verification.status = "cancelled"
    db.commit()

    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost, "new_balance": current_user.credits},
    )
