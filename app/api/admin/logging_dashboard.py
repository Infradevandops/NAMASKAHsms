"""Admin logging dashboard endpoints."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.dependencies import get_admin_user_id
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/logs", tags=["Admin Logs"])


# In-memory log storage for demonstration
# In production, this would be stored in a database or log aggregation service
tier_api_calls = []
tier_402_errors = []
database_errors = []


def log_tier_api_call(user_id: str, endpoint: str, tier: str, status: int):
    """Log a tier API call."""
    tier_api_calls.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "endpoint": endpoint,
        "tier": tier,
        "status": status
    })
    # Keep only last 1000 entries
    if len(tier_api_calls) > 1000:
        tier_api_calls.pop(0)


def log_tier_402_error(user_id: str, endpoint: str, user_tier: str, required_tier: str, reason: str):
    """Log a 402 tier access denied error."""
    tier_402_errors.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "endpoint": endpoint,
        "user_tier": user_tier,
        "required_tier": required_tier,
        "reason": reason
    })
    # Keep only last 1000 entries
    if len(tier_402_errors) > 1000:
        tier_402_errors.pop(0)


def log_database_error(operation: str, error: str, user_id: str = None):
    """Log a database error."""
    database_errors.append({
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "error": error,
        "user_id": user_id
    })
    # Keep only last 1000 entries
    if len(database_errors) > 1000:
        database_errors.pop(0)


@router.get("/tier-api-calls")
async def get_tier_api_calls(
    limit: int = Query(50, ge=1, le=500),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get recent tier API calls (admin only)."""
    logger.info(f"Admin {admin_id} requested tier API call logs")
    
    # Return most recent entries
    return tier_api_calls[-limit:][::-1]  # Reverse to show newest first


@router.get("/tier-402-errors")
async def get_tier_402_errors(
    limit: int = Query(50, ge=1, le=500),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get recent 402 tier access denied errors (admin only)."""
    logger.info(f"Admin {admin_id} requested 402 error logs")
    
    # Return most recent entries
    return tier_402_errors[-limit:][::-1]  # Reverse to show newest first


@router.get("/database-errors")
async def get_database_errors(
    limit: int = Query(50, ge=1, le=500),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get recent database errors (admin only)."""
    logger.info(f"Admin {admin_id} requested database error logs")
    
    # Return most recent entries
    return database_errors[-limit:][::-1]  # Reverse to show newest first


@router.get("/error-trends")
async def get_error_trends(
    days: int = Query(7, ge=1, le=30),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get error trends over time (admin only)."""
    logger.info(f"Admin {admin_id} requested error trends for {days} days")
    
    # Calculate trends from in-memory logs
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff_time.isoformat()
    
    # Count 402 errors by day
    errors_402_by_day = {}
    for error in tier_402_errors:
        if error["timestamp"] >= cutoff_iso:
            day = error["timestamp"][:10]  # Get YYYY-MM-DD
            errors_402_by_day[day] = errors_402_by_day.get(day, 0) + 1
    
    # Count database errors by day
    db_errors_by_day = {}
    for error in database_errors:
        if error["timestamp"] >= cutoff_iso:
            day = error["timestamp"][:10]
            db_errors_by_day[day] = db_errors_by_day.get(day, 0) + 1
    
    # Count 402 errors by required tier
    errors_by_tier = {}
    for error in tier_402_errors:
        if error["timestamp"] >= cutoff_iso:
            tier = error["required_tier"]
            errors_by_tier[tier] = errors_by_tier.get(tier, 0) + 1
    
    return {
        "period_days": days,
        "total_402_errors": len([e for e in tier_402_errors if e["timestamp"] >= cutoff_iso]),
        "total_db_errors": len([e for e in database_errors if e["timestamp"] >= cutoff_iso]),
        "errors_402_by_day": errors_402_by_day,
        "db_errors_by_day": db_errors_by_day,
        "errors_by_required_tier": errors_by_tier
    }


@router.get("/summary")
async def get_logs_summary(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get summary of all logs (admin only)."""
    logger.info(f"Admin {admin_id} requested logs summary")
    
    # Calculate summary statistics
    last_hour = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    last_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    
    return {
        "total_tier_api_calls": len(tier_api_calls),
        "total_402_errors": len(tier_402_errors),
        "total_db_errors": len(database_errors),
        "last_hour": {
            "tier_api_calls": len([c for c in tier_api_calls if c["timestamp"] >= last_hour]),
            "errors_402": len([e for e in tier_402_errors if e["timestamp"] >= last_hour]),
            "db_errors": len([e for e in database_errors if e["timestamp"] >= last_hour])
        },
        "last_24h": {
            "tier_api_calls": len([c for c in tier_api_calls if c["timestamp"] >= last_24h]),
            "errors_402": len([e for e in tier_402_errors if e["timestamp"] >= last_24h]),
            "db_errors": len([e for e in database_errors if e["timestamp"] >= last_24h])
        }
    }
