import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.responses import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/stats", response_model=SuccessResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get referral statistics for current user."""
    try:
        # Count referrals
        referral_count = (
            db.query(User).filter(User.referred_by == current_user.id).count()
        )

        return SuccessResponse(
            message="Referral stats retrieved",
            data={
                "referral_code": current_user.referral_code,
                "referral_link": f"{get_settings().base_url}/register?ref={current_user.referral_code}",
                "total_referred": referral_count,
                "total_earnings": current_user.referral_earnings,
            },
        )
    except Exception as e:
        logger.error(
            f"Error fetching referral stats for user {current_user.id}: {e}",
            exc_info=True,
        )
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail="Failed to fetch referral statistics"
        )


@router.get("/list", response_model=SuccessResponse)
async def list_referrals(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List users referred by current user."""
    try:
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
    except Exception as e:
        logger.error(
            f"Error fetching referral list for user {current_user.id}: {e}",
            exc_info=True,
        )
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Failed to fetch referral list")
