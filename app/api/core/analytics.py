"""Analytics API endpoints.

Provides real-time statistics, status updates, and analytics summaries
for user verifications and spending patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id, get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/real-time-stats")
async def get_real_time_stats(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get real-time user statistics.

    Returns current balance and pending verifications count.

    Args:
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        dict: Real-time statistics including balance and pending count

    Raises:
        HTTPException 404: User not found
        HTTPException 500: Internal server error
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        pending_count = (
            db.query(Verification)
            .filter(Verification.user_id == user_id, Verification.status == "pending")
            .count()
        )

        return {
            "balance": float(user.credits) if user.credits else 0.0,
            "pending_verifications": pending_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching real-time stats for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status-updates")
async def get_status_updates(
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    """Get recent status updates for user verifications.

    Returns list of recent verification status changes in the last 24 hours.

    Args:
        limit: Maximum number of updates to return (1-50)
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        dict: List of recent verification status updates

    Raises:
        HTTPException 500: Internal server error
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        recent_verifications = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id, Verification.updated_at >= cutoff_time
            )
            .order_by(Verification.updated_at.desc())
            .limit(limit)
            .all()
        )

        updates = [
            {
                "id": v.id,
                "service": v.service_name,
                "status": v.status,
                "phone_number": (
                    v.phone_number[-4:] if v.phone_number else None
                ),  # Last 4 digits only
                "updated_at": v.updated_at.isoformat() if v.updated_at else None,
                "cost": float(v.cost) if v.cost else 0.0,
            }
            for v in recent_verifications
        ]

        return {"updates": updates}

    except Exception as e:
        logger.error(
            f"Error fetching status updates for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary")
async def get_analytics_summary(
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get analytics summary with optional date filtering.

    Provides comprehensive analytics including verification counts,
    success rates, spending, and daily breakdowns.

    Args:
        from_date: Start date (ISO format), defaults to 30 days ago
        to_date: End date (ISO format), defaults to now
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        dict: Analytics summary with counts, spending, and breakdowns

    Raises:
        HTTPException 400: Invalid date format
        HTTPException 500: Internal server error
    """
    try:
        # Parse and validate dates
        if not from_date:
            from_dt = datetime.utcnow() - timedelta(days=30)
        else:
            try:
                from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format")

        if not to_date:
            to_dt = datetime.utcnow()
        else:
            try:
                to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format")

        # Validate date range
        if from_dt > to_dt:
            raise HTTPException(
                status_code=400, detail="from_date must be before to_date"
            )

        # Query verifications in date range
        verifications = (
            db.query(Verification)
            .filter(
                Verification.user_id == user_id,
                Verification.created_at >= from_dt,
                Verification.created_at <= to_dt,
            )
            .all()
        )

        # Calculate metrics
        total_verifications = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        failed = sum(
            1
            for v in verifications
            if v.status in ["failed", "timeout", "cancelled", "error"]
        )
        pending = sum(1 for v in verifications if v.status == "pending")

        # Calculate spending
        total_spent = sum(float(v.cost) for v in verifications if v.cost)

        # Top services
        service_counts: Dict[str, int] = {}
        for v in verifications:
            if v.service_name:
                service_counts[v.service_name] = (
                    service_counts.get(v.service_name, 0) + 1
                )

        top_services = [
            {"name": service, "count": count}
            for service, count in sorted(service_counts.items(), key=lambda x: -x[1])[
                :5
            ]
        ]

        # Daily breakdown
        daily_verifications = []
        current_date = from_dt.date()
        while current_date <= to_dt.date():
            count = sum(
                1
                for v in verifications
                if v.created_at and v.created_at.date() == current_date
            )
            daily_verifications.append(
                {"date": current_date.isoformat(), "count": count}
            )
            current_date += timedelta(days=1)

        # Success rate
        success_rate = (
            (successful / total_verifications * 100) if total_verifications > 0 else 0.0
        )

        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful,
            "failed_verifications": failed,
            "pending_verifications": pending,
            "success_rate": round(success_rate, 2),
            "total_spent": round(total_spent, 2),
            "top_services": top_services,
            "daily_verifications": daily_verifications,
            "date_range": {"from": from_dt.isoformat(), "to": to_dt.isoformat()},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error generating analytics summary for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
