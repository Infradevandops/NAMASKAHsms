"""Pricing endpoint for verification services"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.tier_helpers import raise_tier_error
from app.services.tier_manager import TierManager

logger = get_logger(__name__)

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.get("/pricing")
async def get_verification_pricing(
    service: str,
    country: str = "US",
    area_code: str = None,
    carrier: str = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get pricing for verification with optional area code and carrier"""
    try:
        if not service:
            raise HTTPException(status_code=400, detail="Service required")

        tier_manager = TierManager(db)

        # Check area code access (Starter+)
        if area_code and area_code != "any":
            if not tier_manager.check_feature_access(user_id, "area_code_selection"):
                user_tier = tier_manager.get_user_tier(user_id)
                raise_tier_error(user_tier, "starter", user_id)

        # Check ISP/carrier access (Turbo only)
        if carrier and carrier != "any":
            if not tier_manager.check_feature_access(user_id, "isp_filtering"):
                user_tier = tier_manager.get_user_tier(user_id)
                raise_tier_error(user_tier, "turbo", user_id)

        from app.services.textverified_service import TextVerifiedService
        integration = TextVerifiedService()

        # Get real-time pricing from provider
        # This returns the cost 'To Us' from TextVerified
        pricing_data = await integration.get_pricing(
            service=service, 
            country=country,
            area_code=area_code if area_code != "any" else None,
            carrier=carrier if carrier != "any" else None
        )
        provider_cost = pricing_data["cost"]

        # Application Margins / Premiums
        # We add a small markup for premium features on top of provider cost
        margin_percent = 0.10 # 10% base margin
        area_code_markup = 0.10 if area_code and area_code != "any" else 0
        carrier_markup = 0.15 if carrier and carrier != "any" else 0

        total_price = provider_cost * (1 + margin_percent) + area_code_markup + carrier_markup

        return {
            "success": True,
            "service": service,
            "country": country,
            "area_code": area_code or "any",
            "carrier": carrier or "any",
            "provider_cost": round(provider_cost, 2),
            "total_price": round(total_price, 2),
            "currency": "USD",
            "tier_info": {
                "current_tier": tier_manager.get_user_tier(user_id),
                "area_code_available": tier_manager.check_feature_access(
                    user_id, "area_code_selection"
                ),
                "isp_filtering_available": tier_manager.check_feature_access(
                    user_id, "isp_filtering"
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate pricing")
