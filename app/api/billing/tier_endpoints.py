"""Tier management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.tier_manager import TierManager
from app.services.notification_service import NotificationService
from app.core.tier_config import TierConfig
from app.schemas.tier import TierInfo, UserTierInfo, TierUpgradeRequest, TierUpgradeResponse
from app.models.user import User

router = APIRouter(prefix="/api/tiers", tags=["Tiers"])


@router.get("/", response_model=list[TierInfo])
async def list_tiers():
    """List all available subscription tiers."""
    tiers = TierConfig.get_all_tiers()
    
    tier_infos = []
    for tier in tiers:
        # Format price display
        if tier["price_monthly"] == 0:
            price_display = "Free"
        else:
            dollars = tier["price_monthly"] / 100
            price_display = f"${dollars:.2f}/mo"
        
        tier_infos.append(TierInfo(
            name=tier["name"],
            tier=tier["tier"],
            price_monthly=tier["price_monthly"],
            price_display=price_display,
            payment_required=tier["payment_required"],
            has_api_access=tier["has_api_access"],
            has_area_code_selection=tier["has_area_code_selection"],
            has_isp_filtering=tier["has_isp_filtering"],
            api_key_limit=tier["api_key_limit"],
            daily_verification_limit=tier["daily_verification_limit"],
            monthly_verification_limit=tier["monthly_verification_limit"],
            country_limit=tier["country_limit"],
            sms_retention_days=tier["sms_retention_days"],
            support_level=tier["support_level"],
            features=tier["features"]
        ))
    
    return tier_infos


@router.get("/current", response_model=UserTierInfo)
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user's tier information."""
    tier_manager = TierManager(db)
    user_tier = tier_manager.get_user_tier(user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate days remaining for paid tiers
    days_remaining = None
    if user.tier_expires_at:
        delta = user.tier_expires_at - datetime.now()
        days_remaining = max(0, delta.days)
    
    # Determine upgrade options
    upgrade_options = []
    if user_tier == "freemium":
        upgrade_options = ["starter", "turbo"]
    elif user_tier == "starter":
        upgrade_options = ["turbo"]
    
    config = TierConfig.get_tier_config(user_tier)
    
    return UserTierInfo(
        current_tier=user_tier,
        tier_name=config["name"],
        upgraded_at=user.tier_upgraded_at,
        expires_at=user.tier_expires_at,
        days_remaining=days_remaining,
        can_upgrade=len(upgrade_options) > 0,
        upgrade_options=upgrade_options
    )


@router.post("/upgrade", response_model=TierUpgradeResponse)
async def upgrade_tier(
    upgrade_request: TierUpgradeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upgrade user to a higher tier."""
    tier_manager = TierManager(db)
    current_tier = tier_manager.get_user_tier(user_id)
    target_tier = upgrade_request.target_tier
    
    # Validate upgrade path
    tier_hierarchy = {"freemium": 0, "starter": 1, "turbo": 2}
    if tier_hierarchy.get(target_tier, -1) <= tier_hierarchy.get(current_tier, 0):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upgrade from {current_tier} to {target_tier}"
        )
    
    # Get pricing
    target_config = TierConfig.get_tier_config(target_tier)
    price_cents = target_config["price_monthly"]
    
    # TODO: Process payment with Stripe if payment_method_id provided
    # For now, just upgrade the tier (payment integration needed)
    
    success = tier_manager.upgrade_tier(user_id, target_tier)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upgrade tier")
    
    # Notification: Tier Upgraded
    try:
        notif_service = NotificationService(db)
        notif_service.create_notification(
            user_id=user_id,
            notification_type="tier_upgraded",
            title="Tier Upgraded",
            message=f"Successfully upgraded to {target_tier.title()} tier"
        )
    except Exception:
        pass
    
    user = db.query(User).filter(User.id == user_id).first()
    
    return TierUpgradeResponse(
        success=True,
        message=f"Successfully upgraded to {target_tier.title()} tier",
        new_tier=target_tier,
        expires_at=user.tier_expires_at,
        payment_required=target_config["payment_required"],
        amount_charged=price_cents if upgrade_request.payment_method_id else None
    )


@router.post("/downgrade")
async def downgrade_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Downgrade to Freemium tier (cancel subscription)."""
    tier_manager = TierManager(db)
    success = tier_manager.downgrade_tier(user_id, "freemium")
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to downgrade tier")
    
    return {"success": True, "message": "Downgraded to Freemium tier"}
