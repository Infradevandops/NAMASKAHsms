"""Admin logging dashboard endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/logging/status")
async def get_logging_status(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get logging status."""
    try:
        return {"status": "operational"}
    except Exception as e:
        logger.error(f"Failed to get logging status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get logging status")
