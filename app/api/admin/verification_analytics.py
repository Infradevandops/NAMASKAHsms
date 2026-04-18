"""Admin verification analytics endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/verification-analytics/summary")
async def get_verification_analytics_summary(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get verification analytics summary."""
    return {"analytics": "No data available"}


@router.get("/analytics/refunds")
async def get_refund_analytics(
    days: int = 30,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get comprehensive refund analytics (admin only).

    Returns:
        - Total refunds amount and count
        - Refund rate (% of verifications refunded)
        - Net revenue (revenue - refunds)
        - Refund breakdown by reason
        - Average refund amount
    """
    try:
        from app.services.analytics_service import AnalyticsService

        analytics_service = AnalyticsService(db)
        metrics = await analytics_service.get_refund_metrics(days)

        return metrics

    except Exception as e:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Failed to get refund analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve refund analytics"
        )
