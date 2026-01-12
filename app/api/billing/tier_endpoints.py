"""Tier management API endpoints - Updated for 4-tier pricing system."""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.tier_config import TierConfig
from app.models.user import User
from app.models.verification import Verification
from app.models.user_quota import MonthlyQuotaUsage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tiers", tags=["Tiers"])


@router.get("/")
async def list_tiers(db: Session = Depends(get_db)):
    """List all available subscription tiers with pricing."""
    logger.info("Fetching all available tiers")
    try:
        tiers = TierConfig.get_all_tiers(db)
        logger.debug(f"Retrieved {len(tiers)} tiers from config")

        # Format for frontend display
        formatted_tiers = []
        for tier in tiers:
            # Convert price from cents to dollars
            price_monthly_dollars = tier["price_monthly"] / 100 if tier["price_monthly"] else 0
            formatted_tier = {
                "tier": tier["tier"],
                "name": tier["name"],
                "price_monthly": price_monthly_dollars,
                "price_display": "Free" if tier["price_monthly"] == 0 else f"${price_monthly_dollars:.2f}/mo",
                "quota_usd": tier["quota_usd"],
                "overage_rate": tier["overage_rate"],
                "features": {
                    "api_access": tier["has_api_access"],
                    "area_code_selection": tier["has_area_code_selection"],
                    "isp_filtering": tier["has_isp_filtering"],
                    "api_key_limit": tier["api_key_limit"],
                    "support_level": tier["support_level"]
                }
            }
            formatted_tiers.append(formatted_tier)

        logger.info(f"Successfully formatted {len(formatted_tiers)} tiers")
        return {"tiers": formatted_tiers}
    except Exception as e:
        logger.error(f"Failed to fetch tiers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve tier information: {str(e)}"
        )


@router.get("/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user's tier information, quota usage, and pricing."""
    logger.info(f"Fetching current tier for user_id: {user_id}")
    
    try:
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        user_tier = user.subscription_tier or 'freemium'
        logger.debug(f"User {user_id} has tier: {user_tier}")
        
        # Get tier configuration
        try:
            tier_config = TierConfig.get_tier_config(user_tier, db)
            logger.debug(f"Retrieved tier config for {user_tier}: {tier_config.get('name', 'Unknown')}")
        except Exception as config_error:
            logger.error(f"Failed to get tier config for {user_tier}: {str(config_error)}")
            # Use fallback config
            tier_config = TierConfig._get_fallback_config(user_tier)
        
        # Convert price from cents to dollars
        price_monthly_dollars = tier_config["price_monthly"] / 100 if tier_config["price_monthly"] else 0
        
        # Calculate quota usage for current month
        current_month = datetime.utcnow().strftime("%Y-%m")
        quota_used_usd = 0.0
        sms_count = 0
        
        try:
            # Try to get from MonthlyQuotaUsage table first
            monthly_usage = db.query(MonthlyQuotaUsage).filter(
                MonthlyQuotaUsage.user_id == user_id,
                MonthlyQuotaUsage.month == current_month
            ).first()
            
            if monthly_usage:
                quota_used_usd = monthly_usage.quota_used or 0.0
                logger.debug(f"Found monthly quota usage: ${quota_used_usd}")
            else:
                # Fallback: Calculate from user's monthly_quota_used field
                quota_used_usd = user.monthly_quota_used or 0.0
                logger.debug(f"Using user.monthly_quota_used: ${quota_used_usd}")
            
            # Count SMS verifications for current month
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            sms_count = db.query(func.count(Verification.id)).filter(
                Verification.user_id == user_id,
                Verification.created_at >= month_start,
                Verification.capability == "sms"
            ).scalar() or 0
            logger.debug(f"SMS count for current month: {sms_count}")
            
        except Exception as quota_error:
            logger.warning(f"Failed to calculate quota usage: {str(quota_error)}")
            # Continue with defaults
            quota_used_usd = user.monthly_quota_used or 0.0
        
        # Calculate quota remaining and within_quota status
        quota_limit = float(tier_config.get("quota_usd", 0) or 0)  # Convert Decimal to float
        quota_remaining_usd = max(0, quota_limit - quota_used_usd)
        within_quota = quota_used_usd <= quota_limit if quota_limit > 0 else True
        
        logger.info(f"Successfully retrieved tier info for user {user_id}: tier={user_tier}, quota_used=${quota_used_usd}, sms_count={sms_count}")

        return {
            "current_tier": user_tier,
            "tier_name": tier_config["name"],
            "price_monthly": price_monthly_dollars,
            "quota_usd": quota_limit,
            "quota_used_usd": round(quota_used_usd, 2),
            "quota_remaining_usd": round(quota_remaining_usd, 2),
            "sms_count": sms_count,
            "within_quota": within_quota,
            "overage_rate": tier_config["overage_rate"],
            "features": {
                "api_access": tier_config["has_api_access"],
                "area_code_selection": tier_config["has_area_code_selection"],
                "isp_filtering": tier_config["has_isp_filtering"],
                "api_key_limit": tier_config["api_key_limit"],
                "support_level": tier_config["support_level"]
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching tier for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve tier information: {str(e)}"
        )


@router.post("/upgrade")
async def upgrade_tier(
    request_data: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upgrade user to a higher tier."""
    logger.info(f"Upgrade request from user {user_id}: {request_data}")
    
    try:
        target_tier = request_data.get("target_tier")
        if not target_tier:
            logger.warning(f"Upgrade request missing target_tier from user {user_id}")
            raise HTTPException(status_code=400, detail="target_tier required")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for upgrade: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        current_tier = user.subscription_tier or 'freemium'
        logger.debug(f"User {user_id} current tier: {current_tier}, target: {target_tier}")

        # Validate upgrade path
        tier_hierarchy = {"freemium": 0, "payg": 1, "pro": 2, "custom": 3}
        if tier_hierarchy.get(target_tier, -1) <= tier_hierarchy.get(current_tier, 0):
            logger.warning(f"Invalid upgrade path: {current_tier} -> {target_tier}")
            raise HTTPException(
                status_code=400,
                detail=f"Cannot upgrade from {current_tier} to {target_tier}"
            )

        # Get target tier config
        tier_config = TierConfig.get_tier_config(target_tier, db)

        # Payment processing will be implemented in Phase 2
        # For now, just upgrade the tier

        # Update user tier
        user.subscription_tier = target_tier
        user.tier_upgraded_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully upgraded user {user_id} from {current_tier} to {target_tier}")

        # Convert price from cents to dollars
        price_monthly_dollars = tier_config["price_monthly"] / 100 if tier_config["price_monthly"] else 0

        return {
            "success": True,
            "message": f"Successfully upgraded to {tier_config['name']} tier",
            "new_tier": target_tier,
            "price_monthly": price_monthly_dollars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade user {user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upgrade tier: {str(e)}"
        )


@router.post("/downgrade")
async def downgrade_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Downgrade to Freemium tier."""
    logger.info(f"Downgrade request from user {user_id}")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for downgrade: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        previous_tier = user.subscription_tier or 'freemium'
        user.subscription_tier = "freemium"
        db.commit()
        
        logger.info(f"Successfully downgraded user {user_id} from {previous_tier} to freemium")

        return {
            "success": True,
            "message": "Downgraded to Freemium tier",
            "new_tier": "freemium"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to downgrade user {user_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to downgrade tier: {str(e)}"
        )
