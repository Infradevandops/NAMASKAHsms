"""Dashboard Analytics Endpoints - Specific endpoints for dashboard analytics UI."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import csv
from io import StringIO

from app.core.logging import get_logger
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Dashboard Analytics"])


@router.get("/summary")
async def get_analytics_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get analytics summary with statistics cards data."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).all()

        total = len(verifications)
        successful = sum(1 for v in verifications if v.status == "completed")
        active = sum(1 for v in verifications if v.status == "pending")
        
        # Calculate trends
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_verifications = [v for v in verifications if v.created_at >= thirty_days_ago]
        recent_total = len(recent_verifications)
        recent_successful = sum(1 for v in recent_verifications if v.status == "completed")
        
        # Previous 30 days
        sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
        previous_verifications = [
            v for v in verifications 
            if sixty_days_ago <= v.created_at < thirty_days_ago
        ]
        previous_total = len(previous_verifications)

        total_trend = ((recent_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
        success_trend = ((recent_successful - (sum(1 for v in previous_verifications if v.status == "completed"))) / 
                        (sum(1 for v in previous_verifications if v.status == "completed") or 1) * 100)

        return {
            "total_verifications": total,
            "total_trend": round(total_trend, 1),
            "success_rate": round((successful / total * 100) if total > 0 else 0, 1),
            "success_trend": round(success_trend, 1),
            "active_rentals": active,
            "credit_balance": round(user.credits, 2) if user.credits else 0.0
        }

    except Exception as e:
        logger.error(f"Analytics summary error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load analytics summary")


@router.get("/daily-stats")
async def get_daily_stats(
    user_id: str = Depends(get_current_user_id),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    services: Optional[str] = Query(None),
    countries: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get daily statistics for the last 30 days."""
    try:
        # Parse dates
        if date_to:
            end_date = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)
        
        if date_from:
            start_date = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        else:
            start_date = end_date - timedelta(days=30)

        # Build query
        query = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= start_date,
            Verification.created_at <= end_date
        )

        # Apply filters
        if services:
            service_list = services.split(',')
            query = query.filter(Verification.service_name.in_(service_list))
        
        if countries:
            country_list = countries.split(',')
            query = query.filter(Verification.country.in_(country_list))
        
        if status:
            status_list = status.split(',')
            query = query.filter(Verification.status.in_(status_list))

        verifications = query.all()

        # Group by date
        daily_stats = {}
        for v in verifications:
            date_key = v.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_stats:
                daily_stats[date_key] = {"count": 0, "successful": 0, "total": 0}
            daily_stats[date_key]["count"] += 1
            daily_stats[date_key]["total"] += 1
            if v.status == "completed":
                daily_stats[date_key]["successful"] += 1

        # Format response
        result = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            result.append({
                "date": date_key,
                "count": stats["count"],
                "success_rate": round((stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1)
            })

        return result

    except Exception as e:
        logger.error(f"Daily stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load daily statistics")


@router.get("/service-breakdown")
async def get_service_breakdown(
    user_id: str = Depends(get_current_user_id),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get service breakdown statistics."""
    try:
        # Parse dates
        if date_to:
            end_date = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)
        
        if date_from:
            start_date = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        else:
            start_date = end_date - timedelta(days=30)

        # Query service breakdown
        query = db.query(
            Verification.service_name,
            func.count(Verification.id).label("count")
        ).filter(
            Verification.user_id == user_id,
            Verification.created_at >= start_date,
            Verification.created_at <= end_date
        ).group_by(Verification.service_name)

        results = query.all()

        return [
            {
                "service": service,
                "count": count
            }
            for service, count in results
        ]

    except Exception as e:
        logger.error(f"Service breakdown error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load service breakdown")


@router.get("/country-breakdown")
async def get_country_breakdown(
    user_id: str = Depends(get_current_user_id),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get country breakdown statistics."""
    try:
        # Parse dates
        if date_to:
            end_date = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)
        
        if date_from:
            start_date = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        else:
            start_date = end_date - timedelta(days=30)

        # Query country breakdown
        query = db.query(
            Verification.country,
            func.count(Verification.id).label("count")
        ).filter(
            Verification.user_id == user_id,
            Verification.created_at >= start_date,
            Verification.created_at <= end_date,
            Verification.country.isnot(None)
        ).group_by(Verification.country).order_by(func.count(Verification.id).desc())

        results = query.all()

        return [
            {
                "country": country or "Unknown",
                "count": count
            }
            for country, count in results
        ]

    except Exception as e:
        logger.error(f"Country breakdown error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load country breakdown")


@router.post("/export")
async def export_analytics(
    user_id: str = Depends(get_current_user_id),
    format: str = Query("csv"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    services: Optional[str] = Query(None),
    countries: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export analytics data in CSV or PDF format."""
    try:
        # Parse dates
        if date_to:
            end_date = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)
        
        if date_from:
            start_date = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        else:
            start_date = end_date - timedelta(days=30)

        # Build query
        query = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= start_date,
            Verification.created_at <= end_date
        )

        # Apply filters
        if services:
            service_list = services.split(',')
            query = query.filter(Verification.service_name.in_(service_list))
        
        if countries:
            country_list = countries.split(',')
            query = query.filter(Verification.country.in_(country_list))
        
        if status:
            status_list = status.split(',')
            query = query.filter(Verification.status.in_(status_list))

        verifications = query.all()

        if format == "csv":
            # Generate CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Date", "Service", "Country", "Status", "Cost", "Phone Number"
            ])
            
            # Write data
            for v in verifications:
                writer.writerow([
                    v.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    v.service_name,
                    v.country or "Unknown",
                    v.status,
                    f"${v.cost:.2f}",
                    v.phone_number or "N/A"
                ])
            
            return {
                "success": True,
                "format": "csv",
                "data": output.getvalue()
            }

        elif format == "pdf":
            # For PDF, we'll return a message indicating it should be generated client-side
            return {
                "success": True,
                "format": "pdf",
                "message": "PDF export should be generated client-side using jsPDF"
            }

        elif format == "email":
            # For email, we'll return a message indicating it should be sent
            if not email:
                raise HTTPException(status_code=400, detail="Email address required")
            
            return {
                "success": True,
                "format": "email",
                "message": f"Report will be sent to {email}",
                "email": email
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid export format")

    except Exception as e:
        logger.error(f"Export analytics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export analytics")
