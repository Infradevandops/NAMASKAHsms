"""Admin tier management endpoints."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


async def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


@router.get("/tiers/list")
async def list_tiers(admin_id: str = Depends(require_admin)):
    return {
        "tiers": [
            {"name": "freemium", "price": 0},
            {"name": "payg", "price": 0},
            {"name": "pro", "price": 25},
            {"name": "custom", "price": 35},
        ]
    }


@router.get("/tiers/stats")
async def get_tier_stats(admin_id: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Tier distribution stats for admin dashboard."""
    users = db.query(User).filter(User.is_active == True).all()
    counts = {}
    for u in users:
        tier = u.subscription_tier or "freemium"
        counts[tier] = counts.get(tier, 0) + 1
    return {
        "total_users": len(users),
        "by_tier": counts,
        "freemium": counts.get("freemium", 0),
        "payg": counts.get("payg", 0),
        "pro": counts.get("pro", 0),
        "custom": counts.get("custom", 0),
    }


@router.get("/tiers/users")
async def get_tier_users(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tier: str = Query(None),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users with their tier info."""
    query = db.query(User)
    if tier:
        query = query.filter(User.subscription_tier == tier)
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "tier": u.subscription_tier,
                "credits": float(u.credits) if u.credits else 0.0,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/tiers/expiring")
async def get_expiring_tiers(
    days: int = Query(7, ge=1, le=90),
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Users whose tier expires within N days."""
    cutoff = datetime.now(timezone.utc) + timedelta(days=days)
    users = (
        db.query(User)
        .filter(User.tier_expires_at != None, User.tier_expires_at <= cutoff)
        .all()
    )
    return {
        "expiring_within_days": days,
        "count": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "tier": u.subscription_tier,
                "expires_at": u.tier_expires_at.isoformat() if u.tier_expires_at else None,
            }
            for u in users
        ],
    }


class TierUpdateRequest(BaseModel):
    tier: str


@router.put("/tiers/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    body: TierUpdateRequest,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a user's subscription tier."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    valid_tiers = {"freemium", "payg", "pro", "custom"}
    if body.tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")
    user.subscription_tier = body.tier
    db.commit()
    return {"success": True, "user_id": user_id, "new_tier": body.tier}


class BulkTierRequest(BaseModel):
    user_ids: list
    tier: str


@router.post("/tiers/users/bulk/tier")
async def bulk_update_tier(
    body: BulkTierRequest,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk update tier for multiple users."""
    valid_tiers = {"freemium", "payg", "pro", "custom"}
    if body.tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier")
    updated = db.query(User).filter(User.id.in_(body.user_ids)).update(
        {"subscription_tier": body.tier}, synchronize_session=False
    )
    db.commit()
    return {"success": True, "updated": updated, "tier": body.tier}
