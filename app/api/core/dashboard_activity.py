"""Dashboard activity endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity/recent")
async def get_recent_activity(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get recent verification activity for dashboard."""
    logger.info(f"Recent activity requested by user_id: {user_id}")
    
    try:
        # Get user tier for logging
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier or 'freemium' if user else 'unknown'
        logger.debug(f"User {user_id} tier: {user_tier}")
        
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).order_by(desc(Verification.created_at)).limit(10).all()
        
        activities = []
        for v in verifications:
            activities.append({
                "id": v.id,
                "service_name": v.service_name or "Unknown",
                "phone_number": v.phone_number or "N/A",
                "status": v.status or "pending",
                "created_at": v.created_at.isoformat() if v.created_at else None
            })
        
        logger.info(f"Retrieved {len(activities)} recent activities for user {user_id}")
        
        # Return array directly for frontend compatibility
        return activities
        
    except Exception as e:
        logger.error(f"Failed to retrieve recent activity for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent activity: {str(e)}"
        )
