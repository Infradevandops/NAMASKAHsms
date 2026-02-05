"""Enhanced analytics API endpoints with comprehensive metrics."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics Enhanced"])


@router.get("/summary")
async def get_analytics_summary(
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get comprehensive analytics summary for the user."""
    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        f"Analytics summary requested by user_id: {current_user.id}, tier: {current_user.tier or 'freemium'}"
    )
    
    try:
        # Date filtering
        end_date = datetime.utcnow()
        if to_date:
            try:
                end_date = datetime.fromisoformat(to_date.replace("Z", "+00:00")).replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        start_date = end_date - timedelta(days=30)
        if from_date:
            try:
                start_date = datetime.fromisoformat(from_date.replace("Z", "+00:00")).replace(
                    hour=0, minute=0, second=0
                )
            except ValueError:
                pass

        # Base query for period
        verifications_query = db.query(Verification).filter(
            and_(
                Verification.user_id == current_user.id,
                Verification.created_at >= start_date,
                Verification.created_at <= end_date,
            )
        )

        verifications = verifications_query.all()

        # Calculate totals
        total_verifications = len(verifications)
        successful_verifications = len([v for v in verifications if v.status == "completed"])
        failed_verifications = len([v for v in verifications if v.status == "failed"])
        pending_verifications = len([v for v in verifications if v.status in ["pending", "processing"]])

        # Success rate
        success_rate = (successful_verifications / total_verifications) if total_verifications > 0 else 0.0

        # Calculate total spent in period
        spent_transactions = (
            db.query(func.sum(Transaction.amount))
            .filter(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.amount < 0,
                    Transaction.created_at >= start_date,
                    Transaction.created_at <= end_date,
                )
            )
            .scalar()
            or 0
        )
        total_spent = abs(spent_transactions)

        # Average cost per verification
        avg_cost = (total_spent / total_verifications) if total_verifications > 0 else 0.0

        # Monthly metrics
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_verifications = (
            db.query(func.count(Verification.id))
            .filter(
                and_(
                    Verification.user_id == current_user.id,
                    Verification.created_at >= current_month_start,
                )
            )
            .scalar()
            or 0
        )

        monthly_spent_transactions = (
            db.query(func.sum(Transaction.amount))
            .filter(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.amount < 0,
                    Transaction.created_at >= current_month_start,
                )
            )
            .scalar()
            or 0
        )
        monthly_spent = abs(monthly_spent_transactions)

        # Get recent activity (last 10 verifications)
        recent_activity = []
        recent_verifications = (
            db.query(Verification)
            .filter(Verification.user_id == current_user.id)
            .order_by(Verification.created_at.desc())
            .limit(10)
            .all()
        )

        for v in recent_verifications:
            recent_activity.append({
                "id": v.id,
                "service_name": getattr(v, 'service_name', v.service),
                "phone_number": v.phone_number,
                "status": v.status,
                "created_at": v.created_at.isoformat(),
            })

        # Daily verifications for chart
        daily_stats = {}
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_stats[day] = 0

        for v in verifications:
            day = v.created_at.strftime("%Y-%m-%d")
            if day in daily_stats:
                daily_stats[day] += 1

        daily_verifications = [{"date": k, "count": v} for k, v in sorted(daily_stats.items())]

        # Top Services & Spending by Service
        services_map = {}
        for v in verifications:
            svc = getattr(v, 'service_name', v.service) or "Unknown"
            if svc not in services_map:
                services_map[svc] = {"count": 0, "success": 0, "spent": 0.0}

            services_map[svc]["count"] += 1
            if v.status == "completed":
                services_map[svc]["success"] += 1

        top_services = []
        spending_by_service = []

        for name, stats in services_map.items():
            s_rate = (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
            estimated_spend = stats["count"] * avg_cost

            top_services.append({
                "name": name,
                "count": stats["count"],
                "success_rate": s_rate,
                "total_spent": estimated_spend,
            })

            spending_by_service.append({"name": name, "amount": estimated_spend})

        # Sort top services by count
        top_services.sort(key=lambda x: x["count"], reverse=True)
        spending_by_service.sort(key=lambda x: x["amount"], reverse=True)

        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "failed_verifications": failed_verifications,
            "pending_verifications": pending_verifications,
            "success_rate": success_rate,
            "total_spent": total_spent,
            "revenue": total_spent,
            "average_cost": avg_cost,
            "monthly_verifications": monthly_verifications,
            "monthly_spent": monthly_spent,
            "recent_activity": recent_activity,
            "daily_verifications": daily_verifications,
            "top_services": top_services[:10],
            "spending_by_service": spending_by_service[:10],
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Analytics calculation failed for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")


@router.get("/real-time-stats")
async def get_real_time_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get real-time statistics for dashboard updates."""
    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Get pending verifications
        pending_verifications = (
            db.query(Verification)
            .filter(
                and_(
                    Verification.user_id == current_user.id,
                    Verification.status.in_(["pending", "processing"])
                )
            )
            .all()
        )

        updates = []
        for verification in pending_verifications:
            updates.append({
                "id": verification.id,
                "status": verification.status,
                "phone_number": verification.phone_number,
                "created_at": verification.created_at.isoformat(),
            })

        return {
            "pending_count": len(pending_verifications),
            "updates": updates,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Real-time stats failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get real-time stats")
