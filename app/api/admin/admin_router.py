"""Admin router with authentication and authorization."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.tier_config import TierConfig
from app.models.user import User


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Require admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


async def require_moderator_or_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Require moderator or admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or (not user.is_admin and not user.is_moderator):
        raise HTTPException(status_code=403, detail="Moderator or admin access required")
    return user_id


def get_user_role(db, user_id):
    """Get user role."""
    class Role:
        value = "user"
    return Role()


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(user_id: str = Depends(require_admin), db: Session = Depends(get_db)):
    """List all users (admin only)."""
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "is_admin": u.is_admin,
                "is_moderator": getattr(u, 'is_moderator', False),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "credits": u.credits,
                "tier": getattr(u, 'tier', 'freemium'),
            }
            for u in users
        ],
    }


@router.get("/stats")
async def get_admin_stats(user_id: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Get admin statistics."""
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    return {
        "total_users": total_users,
        "admin_users": admin_users,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/tiers")
async def get_tier_info(user_id: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Get tier configuration information."""
    try:
        tiers = TierConfig.get_all_tiers(db)
        return {"tiers": tiers}
    except Exception as e:
        # Fallback to hardcoded tiers if database fails
        fallback_tiers = [
            TierConfig._get_fallback_config(tier) 
            for tier in ["freemium", "payg", "pro", "custom"]
        ]
        return {"tiers": fallback_tiers, "fallback": True}