from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.responses import SuccessResponse

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/stats", response_model=SuccessResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get referral statistics for current user."""
    # Count referrals
    referral_count = db.query(User).filter(User.referred_by == current_user.id).count()

    return SuccessResponse(
        message="Referral stats retrieved",
        data={
            "referral_code": current_user.referral_code,
            "referral_link": f"https://namaskah.com/register?ref={current_user.referral_code}",
            "total_referred": referral_count,
            "total_earnings": current_user.referral_earnings,
            "bonus_credits": current_user.bonus_sms_balance,
        },
    )


@router.get("/list", response_model=SuccessResponse)
async def list_referrals(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List users referred by current user."""
    referrals = db.query(User).filter(User.referred_by == current_user.id).all()

    return SuccessResponse(
        message="Referral list retrieved",
        data=[
            {
                "id": r.id[:8],
                "email": r.email[:3] + "***" + r.email[r.email.find("@") :],
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "status": "Active" if r.email_verified else "Pending",
            }
            for r in referrals
        ],
    )
