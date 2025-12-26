"""Carrier/ISP filtering endpoints (Turbo tier only)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.tier_manager import TierManager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/verification", tags=["Verification"])


@router.get("/carriers/{country}")
async def get_available_carriers(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get list of available carriers/ISPs for a country (Turbo tier only)."""
    tier_manager = TierManager(db)
    
    # Check ISP filtering access
    if not tier_manager.check_feature_access(user_id, "isp_filtering"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_locked",
                "message": "ISP/Carrier filtering is a Turbo tier exclusive feature",
                "feature": "isp_filtering",
                "current_tier": tier_manager.get_user_tier(user_id),
                "required_tier": "turbo",
                "upgrade_url": "/api/tiers/upgrade",
                "upgrade_price": "$13.99/mo"
            }
        )
    
    try:
        # Get carriers from TextVerified integration
        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()
        
        carriers = await integration.get_available_carriers(country)
        
        return {
            "success": True,
            "country": country,
            "carriers": carriers,
            "tier": "turbo"
        }
        
    except Exception as e:
        logger.error(f"Failed to get carriers for {country}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve carrier list"
        )


@router.get("/area-codes/{country}")
async def get_available_area_codes(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get list of available area codes for a country (Starter+ tier)."""
    tier_manager = TierManager(db)
    
    # Check area code access
    if not tier_manager.check_feature_access(user_id, "area_code_selection"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_locked",
                "message": "Area code selection requires Starter tier or higher",
                "feature": "area_code_selection",
                "current_tier": tier_manager.get_user_tier(user_id),
                "required_tier": "starter",
                "upgrade_url": "/api/tiers/upgrade",
                "upgrade_price": "$9/mo"
            }
        )
    
    try:
        # Get area codes from TextVerified integration
        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()
        
        area_codes = await integration.get_available_area_codes(country)
        
        return {
            "success": True,
            "country": country,
            "area_codes": area_codes,
            "tier": tier_manager.get_user_tier(user_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get area codes for {country}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve area code list"
        )
