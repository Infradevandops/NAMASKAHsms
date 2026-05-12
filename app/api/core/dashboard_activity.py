"""Dashboard activity endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/activity")
async def get_recent_activity(
    page: int = 1,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get paginated recent activity for user.

    Args:
        page: Page number (default 1)
        limit: Items per page (default 10)
        user_id: Current user ID
        db: Database session

    Returns:
        dict: Paginated verification activity

    Raises:
        HTTPException 400: Invalid pagination parameters
        HTTPException 500: Database error
    """
    try:
        if page < 1 or limit < 1 or limit > 100:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="Invalid pagination parameters")
        return await _get_activity_internal(user_id, db, page, limit)
    except HTTPException:
        raise
    except Exception as e:
        from fastapi import HTTPException

        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error fetching activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/activity/recent")
async def get_recent_activity_list(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get recent activity list (last 10 items).

    Returns:
        list: Recent verifications

    Raises:
        HTTPException 500: Database error
    """
    try:
        result = await _get_activity_internal(user_id, db, 1, 10)
        return result["verifications"]
    except Exception as e:
        from fastapi import HTTPException

        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error fetching recent activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def _get_activity_internal(user_id: str, db: Session, page: int, limit: int):
    """Internal helper to fetch activity data."""
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    offset = (page - 1) * limit
    try:
        verifications = (
            db.query(Verification)
            .filter(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        total = (
            db.query(func.count(Verification.id))
            .filter(Verification.user_id == user_id)
            .scalar()
            or 0
        )
        return {
            "verifications": [
                {
                    "id": str(v.id),
                    "service_name": v.service_name or "Unknown",
                    "phone_number": v.phone_number or "N/A",
                    "status": v.status or "pending",
                    "cost": float(v.cost) if v.cost else 0.0,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in verifications
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Database error in _get_activity_internal: {e}", exc_info=True)
        return {"verifications": [], "total": 0, "page": page, "limit": limit}
