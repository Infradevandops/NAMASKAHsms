"""Admin user management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin/users", tags=["Admin User Management"])


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/search")
async def search_users(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Search users by email or ID."""
    try:
        search_term = f"%{query}%"
        
        users_query = db.query(User).filter(
            (User.email.ilike(search_term)) | (User.id.ilike(search_term))
        )
        
        total = users_query.count()
        users = users_query.limit(limit).offset(offset).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": query,
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "tier": u.subscription_tier or 'freemium',
                    "is_suspended": getattr(u, 'is_suspended', False),
                    "is_banned": getattr(u, 'is_banned', False),
                    "credits": float(u.credits or 0),
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login": u.last_login.isoformat() if hasattr(u, 'last_login') and u.last_login else None
                }
                for u in users
            ]
        }
    except Exception as e:
        logger.error(f"Search users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search users")


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user activity logs."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get recent verifications
        from app.models.verification import Verification
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).order_by(Verification.created_at.desc()).limit(limit).all()
        
        return {
            "user_id": user_id,
            "email": user.email,
            "tier": user.subscription_tier or 'freemium',
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
            "total_verifications": len(verifications),
            "recent_verifications": [
                {
                    "id": v.id,
                    "country": v.country,
                    "service": v.service_name,
                    "status": v.status,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "cost_usd": float(v.cost or 0)
                }
                for v in verifications[:limit]
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user activity error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user activity")


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    reason: str = Query(..., min_length=1, max_length=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Suspend a user account."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.id == admin_id:
            raise HTTPException(status_code=400, detail="Cannot suspend yourself")
        
        if getattr(user, 'is_suspended', False):
            raise HTTPException(status_code=400, detail="User is already suspended")
        
        user.is_suspended = True
        user.suspended_at = datetime.now(timezone.utc)
        user.suspension_reason = reason
        
        db.commit()
        logger.info(f"Admin {admin_id} suspended user {user_id}. Reason: {reason}")
        
        return {
            "success": True,
            "message": f"User {user_id} suspended",
            "user_id": user_id,
            "suspended_at": user.suspended_at.isoformat() if hasattr(user, 'suspended_at') else None,
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suspend user error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to suspend user")


@router.post("/{user_id}/unsuspend")
async def unsuspend_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Unsuspend a user account."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not getattr(user, 'is_suspended', False):
            raise HTTPException(status_code=400, detail="User is not suspended")
        
        user.is_suspended = False
        user.suspended_at = None
        user.suspension_reason = None
        
        db.commit()
        logger.info(f"Admin {admin_id} unsuspended user {user_id}")
        
        return {
            "success": True,
            "message": f"User {user_id} unsuspended",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unsuspend user error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unsuspend user")


@router.post("/{user_id}/ban")
async def ban_user(
    user_id: str,
    reason: str = Query(..., min_length=1, max_length=500),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Ban a user account permanently."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.id == admin_id:
            raise HTTPException(status_code=400, detail="Cannot ban yourself")
        
        if getattr(user, 'is_banned', False):
            raise HTTPException(status_code=400, detail="User is already banned")
        
        user.is_banned = True
        user.banned_at = datetime.now(timezone.utc)
        user.ban_reason = reason
        
        db.commit()
        logger.info(f"Admin {admin_id} banned user {user_id}. Reason: {reason}")
        
        return {
            "success": True,
            "message": f"User {user_id} banned",
            "user_id": user_id,
            "banned_at": user.banned_at.isoformat() if hasattr(user, 'banned_at') else None,
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ban user error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to ban user")


@router.post("/{user_id}/unban")
async def unban_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Unban a user account."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not getattr(user, 'is_banned', False):
            raise HTTPException(status_code=400, detail="User is not banned")
        
        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None
        
        db.commit()
        logger.info(f"Admin {admin_id} unbanned user {user_id}")
        
        return {
            "success": True,
            "message": f"User {user_id} unbanned",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unban user error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unban user")
