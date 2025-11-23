"""Consolidated SMS Verification API."""
from datetime import datetime, timezone
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.verification import Verification
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])

class SuccessResponse(BaseModel):
    message: str
    data: dict = {}

class VerificationCreate(BaseModel):
    service_name: str
    country: str = "US"
    capability: str = "sms"

class VerificationResponse(BaseModel):
    id: str
    service_name: str
    phone_number: str
    capability: str
    status: str
    cost: float
    created_at: str
    completed_at: str = None

class VerificationHistoryResponse(BaseModel):
    verifications: list
    total_count: int

def create_safe_error_detail(e):
    return str(e)[:100]

@router.get("/services")
async def get_available_services():
    """Get available services."""
    return {
        "success": True,
        "services": [
            {"id": "telegram", "name": "Telegram"},
            {"id": "whatsapp", "name": "WhatsApp"},
            {"id": "google", "name": "Google"},
        ],
        "total": 3
    }

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

        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        base_cost = 0.50

        if current_user.free_verifications > 0:
            current_user.free_verifications -= 1
            actual_cost = 0.0
            db.commit()
        elif current_user.credits >= base_cost:
            current_user.credits -= base_cost
            actual_cost = base_cost
            db.commit()
        else:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        verification = Verification(
            user_id=user_id,
            service_name=verification_data.service_name,
            capability=verification_data.capability,
            status="pending",
            cost=actual_cost,
            phone_number="+1234567890",
            country=verification_data.country,
            verification_code="123",
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
            "created_at": verification.created_at.isoformat(),
            "completed_at": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification creation failed: {create_safe_error_detail(e)}")
        raise HTTPException(status_code=500, detail="Failed to create verification")

@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(verification_id: str, db: Session = Depends(get_db)):
    """Get verification status."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id
    ).first()

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
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None
    }

@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get verification history."""
    verifications = db.query(Verification).filter(
        Verification.user_id == user_id
    ).all()

    return VerificationHistoryResponse(
        verifications=[],
        total_count=len(verifications),
    )

@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel verification."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    verification.status = "cancelled"
    db.commit()

    return SuccessResponse(message="Verification cancelled")
