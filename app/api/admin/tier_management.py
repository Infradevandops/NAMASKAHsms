"""Admin tier management endpoints - Full implementation."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.core.tier_config import TierConfig
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/tiers", tags=["Admin Tier Management"])


class SetUserTierRequest(BaseModel):
    tier: str
    duration_days: int = 30


class BulkTierUpdateRequest(BaseModel):
    user_ids: List[str]
    tier: str
    duration_days: int = 30


class TierStatsResponse(BaseModel):
    tier: str
    user_count: int
    percentage: float


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/stats")
async def get_tier_stats(admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Get tier distribution statistics."""
    try:
        total_users = db.query(User).count()
        if total_users == 0:
            return {"stats": [], "total_users": 0}

        tiers = ["payg", "starter", "pro", "custom"]
        stats = []

        for tier in tiers:
            count = db.query(User).filter(User.subscription_tier == tier).count()
            percentage = (count / total_users * 100) if total_users > 0 else 0
            stats.append({"tier": tier, "user_count": count, "percentage": round(percentage, 2)})

        return {"stats": stats, "total_users": total_users}
    except Exception as e:
        logger.error(f"Tier stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tier statistics")


@router.get("/users")
async def list_users_by_tier(
    tier: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users filtered by tier."""
    try:
        query = db.query(User)

        if tier:
            valid_tiers = ["freemium", "payg", "pro", "custom"]
            if tier not in valid_tiers:
                raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
            query = query.filter(User.subscription_tier == tier)

        total = query.count()
        users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "tier": u.subscription_tier or "freemium",
                    "tier_expires_at": u.tier_expires_at,
                    "credits": float(u.credits or 0),
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.post("/users/{user_id}/tier")
async def set_user_tier(
    user_id: str,
    request: SetUserTierRequest,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Set user tier directly (admin only)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        valid_tiers = ["freemium", "payg", "pro", "custom"]
        if request.tier not in valid_tiers:
            raise HTTPException(
                status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}"
            )

        if request.duration_days < 1 or request.duration_days > 365:
            raise HTTPException(status_code=400, detail="Duration must be between 1 and 365 days")

        old_tier = user.subscription_tier or "freemium"
        user.subscription_tier = request.tier

        if request.tier != "freemium":
            user.tier_expires_at = datetime.now(timezone.utc) + timedelta(
                days=request.duration_days
            )
        else:
            user.tier_expires_at = None

        db.commit()
        logger.info(
            f"Admin {admin_id} changed user {user_id} tier from {old_tier} to {request.tier}"
        )

        return {
            "success": True,
            "message": f"User tier updated from {old_tier} to {request.tier}",
            "user_id": user_id,
            "new_tier": request.tier,
            "expires_at": user.tier_expires_at.isoformat() if user.tier_expires_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set user tier error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user tier")


@router.post("/users/bulk/tier")
async def bulk_update_tier(
    request: BulkTierUpdateRequest,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update tier for multiple users at once."""
    try:
        valid_tiers = ["freemium", "payg", "pro", "custom"]
        if request.tier not in valid_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")

        if len(request.user_ids) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 users per request")

        users = db.query(User).filter(User.id.in_(request.user_ids)).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")

        updated_count = 0
        for user in users:
            user.subscription_tier = request.tier
            if request.tier != "freemium":
                user.tier_expires_at = datetime.now(timezone.utc) + timedelta(
                    days=request.duration_days
                )
            else:
                user.tier_expires_at = None
            updated_count += 1

        db.commit()
        logger.info(f"Admin {admin_id} bulk updated {updated_count} users to {request.tier}")

        return {
            "success": True,
            "message": f"Updated {updated_count} users to {request.tier}",
            "updated_count": updated_count,
            "total_requested": len(request.user_ids),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk tier update error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to bulk update tiers")


@router.get("/users/{user_id}/tier")
async def get_user_tier(
    user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get user's current tier info (admin only)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = user.subscription_tier or "freemium"
        tier_config = TierConfig.get_tier_config(tier, db)

        return {
            "user_id": user_id,
            "email": user.email,
            "current_tier": tier,
            "tier_name": tier_config["name"],
            "expires_at": user.tier_expires_at.isoformat() if user.tier_expires_at else None,
            "is_expired": (
                user.tier_expires_at < datetime.now(timezone.utc) if user.tier_expires_at else False
            ),
            "tier_config": {
                "price_monthly": tier_config["price_monthly"],
                "quota_usd": tier_config["quota_usd"],
                "api_key_limit": tier_config["api_key_limit"],
                "has_api_access": tier_config["has_api_access"],
                "has_area_code_selection": tier_config["has_area_code_selection"],
                "has_isp_filtering": tier_config["has_isp_filtering"],
                "support_level": tier_config["support_level"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user tier error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user tier")


@router.delete("/users/{user_id}/tier")
async def reset_user_tier(
    user_id: str, admin_id: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Reset user to Freemium tier."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_tier = user.subscription_tier or "freemium"
        user.subscription_tier = "freemium"
        user.tier_expires_at = None

        db.commit()
        logger.info(f"Admin {admin_id} reset user {user_id} from {old_tier} to freemium")

        return {
            "success": True,
            "message": f"User tier reset from {old_tier} to Freemium",
            "user_id": user_id,
            "new_tier": "freemium",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset user tier error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reset user tier")


@router.get("/expiring")
async def get_expiring_tiers(
    days: int = Query(7, ge=1, le=90),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get users with tiers expiring within N days."""
    try:
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=days)

        users = (
            db.query(User)
            .filter(
                User.tier_expires_at.isnot(None),
                User.tier_expires_at >= now,
                User.tier_expires_at <= future,
            )
            .order_by(User.tier_expires_at)
            .all()
        )

        return {
            "expiring_in_days": days,
            "count": len(users),
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "tier": u.subscription_tier or "freemium",
                    "expires_at": u.tier_expires_at.isoformat() if u.tier_expires_at else None,
                    "days_until_expiry": (
                        (u.tier_expires_at - now).days if u.tier_expires_at else None
                    ),
                }
                for u in users
            ],
        }
    except Exception as e:
        logger.error(f"Get expiring tiers error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch expiring tiers")


@router.post("/users/{user_id}/tier/extend")
async def extend_tier_expiry(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Extend user's tier expiry date."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = user.subscription_tier or "freemium"
        if tier == "freemium":
            raise HTTPException(status_code=400, detail="Cannot extend Freemium tier")

        old_expiry = user.tier_expires_at
        if user.tier_expires_at:
            user.tier_expires_at = user.tier_expires_at + timedelta(days=days)
        else:
            user.tier_expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        db.commit()
        logger.info(f"Admin {admin_id} extended user {user_id} tier by {days} days")

        return {
            "success": True,
            "message": f"Tier extended by {days} days",
            "user_id": user_id,
            "old_expiry": old_expiry.isoformat() if old_expiry else None,
            "new_expiry": user.tier_expires_at.isoformat() if user.tier_expires_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extend tier error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to extend tier")
