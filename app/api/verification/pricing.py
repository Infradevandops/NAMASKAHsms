"""Pricing endpoint for verification services"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.tier_manager import TierManager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/verification", tags=["Verification"])


@router.get("/pricing")
async def get_verification_pricing(
    service: str,
    area_code: str = None,
    carrier: str = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get pricing for verification with optional area code and carrier"""
    try:
        if not service:
            raise HTTPException(status_code=400, detail="Service required")
        
        tier_manager = TierManager(db)
        
        # Check area code access (Starter+)
        if area_code and area_code != "any":
            if not tier_manager.check_feature_access(user_id, "area_code_selection"):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "feature_locked",
                        "message": "Area code selection requires Starter tier or higher",
                        "feature": "area_code_selection",
                        "current_tier": tier_manager.get_user_tier(user_id),
                        "required_tier": "starter",
                        "upgrade_url": "/api/tiers/upgrade"
                    }
                )
        
        # Check ISP/carrier access (Turbo only)
        if carrier and carrier != "any":
            if not tier_manager.check_feature_access(user_id, "isp_filtering"):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "feature_locked",
                        "message": "ISP/Carrier filtering requires Turbo tier",
                        "feature": "isp_filtering",
                        "current_tier": tier_manager.get_user_tier(user_id),
                        "required_tier": "turbo",
                        "upgrade_url": "/api/tiers/upgrade"
                    }
                )

        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()

        # Get base price from TextVerified
        base_price = await integration.get_service_pricing(service)

        # Calculate premiums
        area_code_premium = 0.15 if area_code and area_code != "any" else 0
        carrier_premium = 0.25 if carrier and carrier != "any" else 0

        total_price = base_price + area_code_premium + carrier_premium

        return {
            "success": True,
            "service": service,
            "area_code": area_code or "any",
            "carrier": carrier or "any",
            "base_price": round(base_price, 2),
            "area_code_premium": round(area_code_premium, 2),
            "carrier_premium": round(carrier_premium, 2),
            "total_price": round(total_price, 2),
            "tier_info": {
                "current_tier": tier_manager.get_user_tier(user_id),
                "area_code_available": tier_manager.check_feature_access(user_id, "area_code_selection"),
                "isp_filtering_available": tier_manager.check_feature_access(user_id, "isp_filtering")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate pricing")
