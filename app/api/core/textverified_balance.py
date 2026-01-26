"""TextVerified balance API endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/api/textverified", tags=["textverified"])


@router.get("/balance")
async def get_textverified_balance(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get TextVerified API balance (admin only)."""
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get TextVerified balance
    tv_service = TextVerifiedService()
    balance_data = await tv_service.get_balance()

    return {
        "balance": balance_data["balance"],
        "currency": balance_data["currency"],
        "source": "textverified_api",
    }
