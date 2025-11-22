"""Personal verification service API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.verification import VerificationCreate, VerificationResponse
from app.services.personal_sms import PersonalSMSService

router = APIRouter(prefix="/personal", tags=["Personal Verification"])


@router.post("/verify/create", response_model=VerificationResponse)
async def create_personal_verification(
    verification: VerificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create personal SMS verification using your own phone numbers."""
    service = PersonalSMSService(db)
    return await service.create_verification(current_user.id, verification)


@router.get("/verify/{verification_id}/messages")
async def get_personal_messages(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get SMS messages for personal verification."""
    service = PersonalSMSService(db)
    return await service.get_messages(verification_id, current_user.id)


@router.post("/numbers/add")
async def add_personal_number(
    phone_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add your personal phone number for verification."""
    service = PersonalSMSService(db)
    return await service.add_personal_number(current_user.id, phone_number)
