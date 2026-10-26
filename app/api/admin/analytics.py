"""Analytics API endpoints for admin dashboard."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_admin_user_id
from app.models.user import User
from app.models.user_event import UserEvent
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.services.event_tracking_service import EventTrackingService

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])


@router.get("/overview")
def get_analytics_overview(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Get analytics overview dashboard data."""
    try:
        # Total users
        total_users = db.query(User).count()

        # New users (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        new_users_30d = (
            db.query(User)
            .filter(User.created_at >= thirty_days_ago)
            .count()
        )

        # Active users (had event in last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_users_7d = (
            db.query(UserEvent.user_id)
            .filter(UserEvent.created_at >= seven_days_ago)
            .distinct()
            .count()
        )

        # Total verifications
        total_verifications = db.query(Verification).count()

        # Successful verifications
        successful_verifications = (
            db.query(Verification)
            .filter(Verification.status == "completed")
            .count()
        )

        # Success rate
        success_rate = (
            (successful_verifications / total_verifications * 100)
            if total_verifications > 0
            else 0
        )

        # Total revenue (last 30 days)
        total_revenue = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.type == "debit",
                Transaction.created_at >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        # Average verification cost
        avg_cost = (
            db.query(func.avg(Verification.cost))
            .filter(Verification.cost > 0)
            .scalar()
            or 0
        )

        return {
            "total_users": total_users,
            "new_users_30d": new_users_30d,
            "active_users_7d": active_users_7d,
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "success_rate": round(success_rate, 2),
            "total_revenue_30d": float(total_revenue),
            "avg_verification_cost": float(avg_cost),
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_users": 0,
            "new_users_30d": 0,
            "active_users_7d": 0,
            "total_verifications": 0,
            "successful_verifications": 0,
            "success_rate": 0,
            "total_revenue_30d": 0,
            "avg_verification_cost": 0,
        }


@router.get("/users/cohorts")
def get_cohort_analysis(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Get user cohort retention analysis."""
    try:
        # Get users grouped by signup date
        cohorts = (
            db.query(
                func.date(User.created_at).label("cohort_date"),
                func.count(User.id).label("cohort_size"),
            )
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at).desc())
            .limit(30)
            .all()
        )

        result = []
        for cohort_date, cohort_size in cohorts:
            # Get users from this cohort
            cohort_users = (
                db.query(User.id)
                .filter(
                    func.date(User.created_at) == cohort_date,
                )
                .all()
            )
            user_ids = [u[0] for u in cohort_users]

            if not user_ids:
                continue

            # Calculate retention at different days
            day_1_retention = (
                db.query(UserEvent)
                .filter(
                    UserEvent.user_id.in_(user_ids),
                    UserEvent.created_at >= datetime.combine(cohort_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                    UserEvent.created_at < datetime.combine(cohort_date + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc),
                )
                .distinct(UserEvent.user_id)
                .count()
            )

            day_7_retention = (
                db.query(UserEvent)
                .filter(
                    UserEvent.user_id.in_(user_ids),
                    UserEvent.created_at >= datetime.combine(cohort_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                    UserEvent.created_at < datetime.combine(cohort_date + timedelta(days=7), datetime.min.time()).replace(tzinfo=timezone.utc),
                )
                .distinct(UserEvent.user_id)
                .count()
            )

            day_30_retention = (
                db.query(UserEvent)
                .filter(
                    UserEvent.user_id.in_(user_ids),
                    UserEvent.created_at >= datetime.combine(cohort_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                    UserEvent.created_at < datetime.combine(cohort_date + timedelta(days=30), datetime.min.time()).replace(tzinfo=timezone.utc),
                )
                .distinct(UserEvent.user_id)
                .count()
            )

            result.append({
                "cohort_date": str(cohort_date),
                "cohort_size": cohort_size,
                "day_1_retention": round((day_1_retention / cohort_size * 100) if cohort_size > 0 else 0, 2),
                "day_7_retention": round((day_7_retention / cohort_size * 100) if cohort_size > 0 else 0, 2),
                "day_30_retention": round((day_30_retention / cohort_size * 100) if cohort_size > 0 else 0, 2),
            })

        return {"cohorts": result}
    except Exception as e:
        return {"error": str(e), "cohorts": []}


@router.get("/users/at-risk")
def get_at_risk_users(
    admin_id: str = Depends(get_admin_user_id),
    days_inactive: int = Query(7, ge=1, le=90),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get users at risk of churn (inactive for N days)."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)

        # Get users with no events in the last N days
        at_risk_users = (
            db.query(User)
            .filter(
                ~User.id.in_(
                    db.query(UserEvent.user_id).filter(
                        UserEvent.created_at >= cutoff_date
                    )
                )
            )
            .limit(limit)
            .all()
        )

        result = []
        for user in at_risk_users:
            # Get last event
            last_event = (
                db.query(UserEvent)
                .filter(UserEvent.user_id == user.id)
                .order_by(UserEvent.created_at.desc())
                .first()
            )

            # Get verification count
            verification_count = (
                db.query(Verification)
                .filter(Verification.user_id == user.id)
                .count()
            )

            result.append({
                "user_id": str(user.id),
                "email": user.email,
                "credits": float(user.credits),
                "last_activity": last_event.created_at.isoformat() if last_event else None,
                "verification_count": verification_count,
                "days_inactive": (datetime.now(timezone.utc) - (last_event.created_at if last_event else user.created_at)).days,
            })

        return {"at_risk_users": result, "count": len(result)}
    except Exception as e:
        return {"error": str(e), "at_risk_users": [], "count": 0}


@router.get("/events/live")
def get_live_events(
    admin_id: str = Depends(get_admin_user_id),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get recent events for live feed."""
    try:
        query = db.query(UserEvent)

        if event_type:
            query = query.filter(UserEvent.event_type == event_type)

        events = (
            query.order_by(UserEvent.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for event in events:
            user = db.query(User).filter(User.id == event.user_id).first()
            result.append({
                "id": str(event.id),
                "user_id": str(event.user_id),
                "user_email": user.email if user else "Unknown",
                "event_type": event.event_type,
                "event_data": event.event_data,
                "created_at": event.created_at.isoformat(),
            })

        return {"events": result, "count": len(result)}
    except Exception as e:
        return {"error": str(e), "events": [], "count": 0}


@router.get("/events/stats")
def get_event_stats(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Get event statistics."""
    try:
        service = EventTrackingService(db)
        stats = service.get_event_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}


@router.get("/revenue/daily")
def get_daily_revenue(
    admin_id: str = Depends(get_admin_user_id),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get daily revenue breakdown."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        daily_revenue = (
            db.query(
                func.date(Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("revenue"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .filter(
                Transaction.type == "debit",
                Transaction.created_at >= cutoff_date,
            )
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at).desc())
            .all()
        )

        result = []
        for date, revenue, count in daily_revenue:
            result.append({
                "date": str(date),
                "revenue": float(revenue or 0),
                "transaction_count": count,
            })

        return {"daily_revenue": result}
    except Exception as e:
        return {"error": str(e), "daily_revenue": []}


@router.get("/services/popular")
def get_popular_services(
    admin_id: str = Depends(get_admin_user_id),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get most popular services."""
    try:
        popular = (
            db.query(
                Verification.service_name,
                func.count(Verification.id).label("count"),
                func.avg(Verification.cost).label("avg_cost"),
            )
            .filter(Verification.service_name.isnot(None))
            .group_by(Verification.service_name)
            .order_by(func.count(Verification.id).desc())
            .limit(limit)
            .all()
        )

        result = []
        for service, count, avg_cost in popular:
            result.append({
                "service": service,
                "count": count,
                "avg_cost": float(avg_cost or 0),
            })

        return {"popular_services": result}
    except Exception as e:
        return {"error": str(e), "popular_services": []}
