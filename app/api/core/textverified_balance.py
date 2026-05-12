"""TextVerified balance API endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/api/textverified", tags=["textverified"])
_tv_service = TextVerifiedService()


@router.get("/balance")
async def get_textverified_balance(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get TextVerified API balance (Admin only).

    Returns:
        dict: Balance information with amount and currency

    Raises:
        HTTPException 403: Non-admin user
        HTTPException 500: API error
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        balance_data = await _tv_service.get_balance()

        if not balance_data:
            raise HTTPException(status_code=500, detail="Failed to fetch balance")

        return {
            "balance": balance_data.get("balance", 0),
            "currency": balance_data.get("currency", "USD"),
            "source": "textverified_api",
        }
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error fetching TextVerified balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
