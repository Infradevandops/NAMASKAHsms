"""Carrier/ISP filtering endpoints (requires payg tier or higher)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user_id, require_tier
from app.services.tier_manager import TierManager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/verification", tags=["Verification"])

# Tier dependency for payg+ access
require_payg = require_tier("payg")


@router.get("/carriers/{country}")
async def get_available_carriers(
    country: str,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db)
):
    """Get list of available carriers/ISPs for a country (requires payg tier or higher)."""
    logger.info(f"Carrier list requested by user_id: {user_id}, country: {country}")
    
    tier_manager = TierManager(db)
    
    # Check ISP filtering access (pro tier feature)
    if not tier_manager.check_feature_access(user_id, "isp_filtering"):
        user_tier = tier_manager.get_user_tier(user_id)
        logger.warning(
            f"ISP filtering access denied - user_id: {user_id}, "
            f"user_tier: {user_tier}, required_tier: pro, "
            f"reason: feature_locked"
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_locked",
                "message": "ISP/Carrier filtering is a Pro tier exclusive feature",
                "feature": "isp_filtering",
                "current_tier": user_tier,
                "required_tier": "pro",
                "upgrade_url": "/pricing"
            }
        )
    
    try:
        # Get carriers from TextVerified integration
        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()
        
        carriers = await integration.get_available_carriers(country)
        
        logger.info(f"Retrieved {len(carriers) if carriers else 0} carriers for {country}, user_id: {user_id}")
        
        return {
            "success": True,
            "country": country,
            "carriers": carriers,
            "tier": "turbo"
        }
        
    except Exception as e:
        logger.error(f"Failed to get carriers for {country}, user_id: {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve carrier list"
        )


@router.get("/area-codes/{country}")
async def get_available_area_codes(
    country: str,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db)
):
    """Get list of available area codes for a country (requires payg tier or higher)."""
    logger.info(f"Area codes requested by user_id: {user_id}, country: {country}")
    
    tier_manager = TierManager(db)
    
    # Check area code access
    if not tier_manager.check_feature_access(user_id, "area_code_selection"):
        user_tier = tier_manager.get_user_tier(user_id)
        logger.warning(
            f"Area code access denied - user_id: {user_id}, "
            f"user_tier: {user_tier}, required_tier: payg, "
            f"reason: feature_locked"
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_locked",
                "message": "Area code selection requires payg tier or higher",
                "feature": "area_code_selection",
                "current_tier": user_tier,
                "required_tier": "payg",
                "upgrade_url": "/pricing"
            }
        )
    
    try:
        # Get area codes from TextVerified integration
        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()
        
        area_codes = await integration.get_available_area_codes(country)
        
        logger.info(f"Retrieved {len(area_codes) if area_codes else 0} area codes for {country}, user_id: {user_id}")
        
        return {
            "success": True,
            "country": country,
            "area_codes": area_codes,
            "tier": tier_manager.get_user_tier(user_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get area codes for {country}, user_id: {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve area code list"
        )
