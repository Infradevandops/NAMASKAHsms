"""Affiliate program API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_admin_user
from app.services.affiliate_service import affiliate_service
from app.models.user import User
from pydantic import BaseModel, EmailStr
from typing import List, Optional

router = APIRouter(prefix="/affiliate", tags=["affiliate"])

class AffiliateApplicationCreate(BaseModel):
    email: EmailStr
    program_type: str  # 'referral' or 'enterprise'
    program_options: List[str]
    message: Optional[str] = None

class AffiliateApplicationResponse(BaseModel):
    success: bool
    message: str
    application_id: Optional[int] = None

@router.post("/apply", response_model=AffiliateApplicationResponse)
async def apply_for_affiliate_program(
    application: AffiliateApplicationCreate,
    db: Session = Depends(get_db)
):
    """Submit affiliate program application."""
    try:
        result = await affiliate_service.create_application(
            email=application.email,
            program_type=application.program_type,
            program_options=application.program_options,
            message=application.message,
            db=db
        )
        return AffiliateApplicationResponse(
            success=True,
            message="Application submitted successfully! We'll contact you within 24 hours.",
            application_id=result["id"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/programs")
async def get_affiliate_programs(db: Session = Depends(get_db)):
    """Get available affiliate programs."""
    return await affiliate_service.get_available_programs(db)

@router.get("/applications")
async def get_affiliate_applications(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all affiliate applications (admin only)."""
    return await affiliate_service.get_all_applications(db)

@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    status: str,
    admin_notes: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update affiliate application status (admin only)."""
    try:
        result = await affiliate_service.update_application_status(
            application_id=application_id,
            status=status,
            admin_notes=admin_notes,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))