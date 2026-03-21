"""Tier management endpoints for billing operations."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger, log_tier_access
from app.core.tier_config import TierConfig
from app.models.user import User
from app.services.tier_manager import TierManager

logger = get_logger(__name__)
router = APIRouter()


@router.get("/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current tier information for user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tier_manager = TierManager(db)
        tier = tier_manager.get_user_tier(user_id)
        tier_config = TierConfig.get_tier_config(tier, db)

        # Log tier access
        log_tier_access(user_id, tier, "tier_info", True)

        return {
            "current_tier": tier,
            "tier_info": tier_config,
            "user_id": user_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current tier for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tier information"
        )


@router.get("/available")
async def get_available_tiers(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get all available tiers."""
    try:
        tiers = TierConfig.get_all_tiers(db)

        return {
            "available_tiers": tiers,
            "current_user": user_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get available tiers: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve available tiers"
        )


@router.post("/upgrade")
async def upgrade_tier(
    target_tier: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upgrade user to a higher tier."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        available_tiers = ["freemium", "payg", "pro", "custom"]
        if target_tier not in available_tiers:
            raise HTTPException(status_code=400, detail="Invalid tier")

        tier_manager = TierManager(db)
        current_tier = tier_manager.get_user_tier(user_id)

        tier_hierarchy = {"freemium": 0, "payg": 1, "pro": 2, "custom": 3}
        if tier_hierarchy.get(target_tier, 0) <= tier_hierarchy.get(current_tier, 0):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot upgrade to '{target_tier}' from '{current_tier}'",
            )

        # PAYG is free — commit immediately
        if target_tier == "payg":
            user.subscription_tier = target_tier
            db.commit()
            return {
                "message": f"Upgraded to {target_tier}",
                "current_tier": target_tier,
                "target_tier": target_tier,
                "status": "success",
                "user_id": user_id,
            }

        # Paid tiers — initialize Paystack transaction
        from app.services.payment_service import PaymentService

        tier_config = TierConfig.get_tier_config(target_tier, db)
        monthly_fee = tier_config.get("monthly_fee_usd", 0)

        payment_service = PaymentService(db)
        payment_result = await payment_service.initialize_payment(
            user_id=user_id,
            email=user.email,
            amount_usd=monthly_fee,
            metadata={"upgrade_to": target_tier, "user_id": user_id},
        )

        return {
            "message": f"Complete payment to upgrade to {target_tier}",
            "current_tier": current_tier,
            "target_tier": target_tier,
            "status": "pending_payment",
            "authorization_url": payment_result["authorization_url"],
            "reference": payment_result["reference"],
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade tier for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process tier upgrade")


@router.post("/cancel")
async def cancel_subscription(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Cancel paid subscription — access continues until period end, then downgrades to freemium."""
    from app.models.user_preference import UserPreference

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tier = getattr(user, "subscription_tier", "freemium")
    if tier in ("freemium", "payg"):
        raise HTTPException(
            status_code=400, detail="No active paid subscription to cancel"
        )

    # tier_expires_at already set from upgrade webhook — downgrade happens naturally
    # when get_user_tier() detects expiry. Just clear renewal so it won't re-bill.
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if pref:
        pref.subscription_renews_at = None
        db.commit()

    expires_at = getattr(user, "tier_expires_at", None)
    return {
        "success": True,
        "message": "Subscription cancelled. Access continues until period end.",
        "effective_date": expires_at.isoformat() if expires_at else None,
        "current_tier": tier,
    }
