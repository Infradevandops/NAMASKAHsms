"""Pricing endpoints for billing operations."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


@router.get("/current")
async def get_current_pricing(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current pricing for user's tier."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier = getattr(user, 'tier', 'freemium')
        
        # Basic pricing structure
        pricing = {
            "freemium": {
                "tier": "freemium",
                "base_cost": 2.50,
                "monthly_fee": 0.0,
                "free_verifications": 3,
                "overage_rate": 2.22
            },
            "payg": {
                "tier": "payg",
                "base_cost": 2.50,
                "monthly_fee": 0.0,
                "free_verifications": 0,
                "overage_rate": 2.50
            },
            "pro": {
                "tier": "pro",
                "base_cost": 2.50,
                "monthly_fee": 25.0,
                "free_verifications": 0,
                "overage_rate": 0.30
            },
            "custom": {
                "tier": "custom",
                "base_cost": 2.50,
                "monthly_fee": 35.0,
                "free_verifications": 0,
                "overage_rate": 0.20
            }
        }

        return {
            "user_tier": tier,
            "pricing": pricing.get(tier, pricing["freemium"]),
            "currency": "USD",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pricing")


@router.get("/tiers")
async def get_all_tier_pricing(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get pricing for all available tiers."""
    try:
        tiers = [
            {
                "tier": "freemium",
                "name": "Freemium",
                "monthly_fee": 0.0,
                "base_cost": 2.50,
                "free_verifications": 3,
                "features": ["Basic SMS verification", "Community support"]
            },
            {
                "tier": "payg",
                "name": "Pay-As-You-Go",
                "monthly_fee": 0.0,
                "base_cost": 2.50,
                "free_verifications": 0,
                "features": ["SMS verification", "Area code selection", "Community support"]
            },
            {
                "tier": "pro",
                "name": "Pro",
                "monthly_fee": 25.0,
                "base_cost": 2.50,
                "free_verifications": 0,
                "features": ["SMS verification", "API access", "Webhooks", "Priority support"]
            },
            {
                "tier": "custom",
                "name": "Custom",
                "monthly_fee": 35.0,
                "base_cost": 2.50,
                "free_verifications": 0,
                "features": ["All Pro features", "Custom branding", "Dedicated support"]
            }
        ]

        return {
            "tiers": tiers,
            "currency": "USD",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get tier pricing: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tier pricing")
