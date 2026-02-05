"""Tier management endpoints for billing operations."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.tier_config import TierConfig
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


@router.get("/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current tier information for user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = getattr(user, 'tier', 'freemium')
        tier_config = TierConfig.get_tier_config(tier, db)

        return {
            "current_tier": tier,
            "tier_info": tier_config,
            "user_id": user_id,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current tier for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tier information")


@router.get("/available")
async def get_available_tiers(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all available tiers."""
    try:
        tiers = TierConfig.get_all_tiers(db)
        
        return {
            "available_tiers": tiers,
            "current_user": user_id,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get available tiers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available tiers")


@router.post("/upgrade")
async def upgrade_tier(
    target_tier: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upgrade user to a higher tier."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate target tier
        available_tiers = ["freemium", "payg", "pro", "custom"]
        if target_tier not in available_tiers:
            raise HTTPException(status_code=400, detail="Invalid tier")

        current_tier = getattr(user, 'tier', 'freemium')
        if current_tier == target_tier:
            raise HTTPException(status_code=400, detail="Already on this tier")

        # For now, just return success message
        # In a real implementation, this would handle payment processing
        return {
            "message": f"Tier upgrade initiated from {current_tier} to {target_tier}",
            "current_tier": current_tier,
            "target_tier": target_tier,
            "status": "pending_payment",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade tier for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process tier upgrade")
