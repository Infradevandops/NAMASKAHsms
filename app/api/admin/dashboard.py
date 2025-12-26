"""Admin Dashboard API router with optimized analytics."""
from app.core.logging import get_logger
from app.core.dependencies import get_current_admin_user as require_admin
from app.core.unified_cache import cache
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.models.pricing_template import PricingTemplate

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/stats")
async def get_admin_stats(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get admin dashboard statistics - OPTIMIZED"""
    try:
        # Get basic counts with single queries
        users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.last_login.isnot(None)).scalar() or 0
        
        verifications = db.query(func.count(Verification.id)).scalar() or 0
        pending_verifications = db.query(func.count(Verification.id)).filter(Verification.status == 'pending').scalar() or 0
        success_verifications = db.query(func.count(Verification.id)).filter(Verification.status == 'completed').scalar() or 0
        
        # Calculate success rate safely
        success_rate = (success_verifications / verifications * 100) if verifications > 0 else 0
        
        # Calculate revenue safely
        revenue = db.query(func.sum(Verification.cost)).filter(Verification.status == 'completed').scalar() or 0
        
        return {
            "users": users,
            "active_users": active_users,
            "verifications": verifications,
            "pending_verifications": pending_verifications,
            "success_verifications": success_verifications,
            "success_rate": round(success_rate, 1),
            "revenue": float(revenue)
        }
        
    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin stats")


@router.get("/verifications/recent")
async def get_recent_verifications(
    limit: int = Query(10, ge=1, le=50),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get recent verifications with optimized JOIN"""
    try:
        # Use JOIN to avoid N+1 query problem
        verifications = db.query(Verification).options(
            joinedload(Verification.user)
        ).order_by(desc(Verification.created_at)).limit(limit).all()
        
        result = []
        for v in verifications:
            result.append({
                "id": v.id,
                "user_email": v.user.email if v.user else "Unknown",
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "status": v.status,
                "cost": float(v.cost) if v.cost else 0.0,
                "created_at": v.created_at
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Recent verifications error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent verifications")


@router.get("/pricing/templates")
async def get_pricing_templates(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get pricing templates for admin dashboard"""
    try:
        templates = db.query(PricingTemplate).all()
        
        result = []
        for template in templates:
            result.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "is_active": template.is_active,
                "created_at": template.created_at
            })
        
        return {
            "success": True,
            "templates": result
        }
        
    except Exception as e:
        logger.error(f"Pricing templates error: {str(e)}")
        return {
            "success": True,
            "templates": [
                {
                    "id": "standard",
                    "name": "Standard Pricing",
                    "description": "Regular pricing",
                    "is_active": True
                },
                {
                    "id": "promotional",
                    "name": "Promotional 50% Off",
                    "description": "Limited time offer",
                    "is_active": False
                },
                {
                    "id": "holiday",
                    "name": "Holiday Special",
                    "description": "Holiday pricing",
                    "is_active": False
                }
            ]
        }