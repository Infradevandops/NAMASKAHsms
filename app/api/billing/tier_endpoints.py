"""Tier management API endpoints - Updated for 4-tier pricing system."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.pricing_calculator import PricingCalculator
from app.core.tier_config import TierConfig
from app.models.user import User

router = APIRouter(prefix="/api/tiers", tags=["Tiers"])


@router.get("/")
async def list_tiers(db: Session = Depends(get_db)):
    """List all available subscription tiers with pricing."""
    calculator = PricingCalculator(db)
    tiers = calculator.get_all_tiers()

    # Format for frontend display
    formatted_tiers = []
    for tier in tiers:
        formatted_tier = {
            "tier": tier["tier"],
            "name": tier["name"],
            "price_monthly": tier["price_monthly"],
            "price_display": "Free" if tier["price_monthly"] == 0 else f"${tier['price_monthly']:.2f}/mo",
            "quota_usd": tier["quota_usd"],
            "quota_sms": tier.get("quota_sms", 0),
            "overage_rate": tier["overage_rate"],
            "cost_per_sms": tier.get("cost_per_sms", tier.get("overage_cost", 0)),
            "features": {
                "api_access": tier["has_api_access"],
                "area_code_selection": tier["has_area_code_selection"],
                "isp_filtering": tier["has_isp_filtering"],
                "api_key_limit": tier["api_key_limit"],
                "support_level": tier["support_level"]
            }
        }
        formatted_tiers.append(formatted_tier)

    return {"tiers": formatted_tiers}


@router.get("/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user's tier information and pricing."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_tier = getattr(user, 'tier_id', 'payg') or 'payg'

    calculator = PricingCalculator(db)
    pricing_summary = calculator.get_pricing_summary(user_id, user_tier)

    return {
        "current_tier": user_tier,
        "tier_name": pricing_summary["tier"]["name"],
        "price_monthly": pricing_summary["tier"]["price_monthly"],
        "quota_usd": pricing_summary["tier"]["quota_usd"],
        "quota_used_usd": pricing_summary["monthly_usage"]["quota_used_usd"],
        "quota_remaining_usd": max(0, pricing_summary["tier"]["quota_usd"] - pricing_summary["monthly_usage"]["quota_used_usd"]),
        "sms_count": pricing_summary["monthly_usage"]["sms_count"],
        "next_sms_cost": pricing_summary["next_sms_cost"]["cost_per_sms"],
        "within_quota": pricing_summary["next_sms_cost"]["within_quota"],
        "features": pricing_summary["features"]
    }


@router.post("/upgrade")
async def upgrade_tier(
    request_data: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upgrade user to a higher tier."""
    target_tier = request_data.get("target_tier")
    if not target_tier:
        raise HTTPException(status_code=400, detail="target_tier required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_tier = getattr(user, 'tier_id', 'payg') or 'payg'

    # Validate upgrade path
    tier_hierarchy = {"payg": 0, "starter": 1, "pro": 2, "custom": 3}
    if tier_hierarchy.get(target_tier, -1) <= tier_hierarchy.get(current_tier, 0):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upgrade from {current_tier} to {target_tier}"
        )

    # Get target tier config
    tier_config = TierConfig.get_tier_config(target_tier, db)

    # Payment processing will be implemented in Phase 2
    # For now, just upgrade the tier

    # Update user tier
    user.tier_id = target_tier
    db.commit()

    return {
        "success": True,
        "message": f"Successfully upgraded to {tier_config['name']} tier",
        "new_tier": target_tier,
        "price_monthly": tier_config["price_monthly"] / 100
    }


@router.post("/downgrade")
async def downgrade_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Downgrade to Pay-As-You-Go tier."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.tier_id = "payg"
    db.commit()

    return {
        "success": True,
        "message": "Downgraded to Pay-As-You-Go tier",
        "new_tier": "payg"
    }
