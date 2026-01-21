"""Carrier/ISP filtering endpoints (requires payg tier or higher)."""

import textverified
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_tier
from app.core.logging import get_logger
from app.core.tier_helpers import raise_tier_error
from app.services.tier_manager import TierManager

logger = get_logger(__name__)

router = APIRouter(prefix="/verification", tags=["Verification"])

# Tier dependency for payg+ access
require_payg = require_tier("payg")


@router.get("/carriers/{country}")
async def get_available_carriers(
    country: str, user_id: str = Depends(require_payg), db: Session = Depends(get_db)
):
    """Get list of available carriers/ISPs for a country (requires payg tier or higher)."""
    logger.info(f"Carrier list requested by user_id: {user_id}, country: {country}")

    tier_manager = TierManager(db)

    # Check ISP filtering access (pro tier feature)
    if not tier_manager.check_feature_access(user_id, "isp_filtering"):
        user_tier = tier_manager.get_user_tier(user_id)
        raise_tier_error(user_tier, "pro", user_id)

    try:
        # Get carriers from TextVerified integration
        from app.services.textverified_service import TextVerifiedService

        integration = TextVerifiedService()

        carriers = await integration.get_available_carriers(country)

        logger.info(
            f"Retrieved {len(carriers) if carriers else 0} carriers for {country}, user_id: {user_id}"
        )

        return {
            "success": True,
            "country": country,
            "carriers": carriers,
            "tier": "turbo",
        }

    except Exception as e:
        logger.error(
            f"Failed to get carriers for {country}, user_id: {user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve carrier list")


@router.get("/area-codes/{country}")
async def get_available_area_codes(
    country: str, user_id: str = Depends(require_payg), db: Session = Depends(get_db)
):
    """Get list of available area codes for a country (requires payg tier or higher)."""
    logger.info(f"Area codes requested by user_id: {user_id}, country: {country}")

    tier_manager = TierManager(db)

    # Check area code access
    if not tier_manager.check_feature_access(user_id, "area_code_selection"):
        user_tier = tier_manager.get_user_tier(user_id)
        raise_tier_error(user_tier, "payg", user_id)

    try:
        # Get area codes from TextVerified integration
        from app.services.textverified_service import TextVerifiedService

        integration = TextVerifiedService()

        # Get area codes with state information
        if hasattr(integration.client, "services"):
            # Get services to find area codes
            services_data = integration.client.services.list(
                number_type=textverified.NumberType.MOBILE,
                reservation_type=textverified.ReservationType.VERIFICATION,
            )
            
            # Extract unique area codes
            area_codes = []
            seen = set()
            
            # Note: TextVerified API returns area codes per service
            # For now, return a static list of common US area codes with states
            if country.upper() == "US":
                area_codes = [
                    # New York
                    {"area_code": "212", "state": "NY", "city": "New York City"},
                    {"area_code": "917", "state": "NY", "city": "New York City"},
                    # California
                    {"area_code": "213", "state": "CA", "city": "Los Angeles"},
                    {"area_code": "310", "state": "CA", "city": "Los Angeles"},
                    {"area_code": "415", "state": "CA", "city": "San Francisco"},
                    # Illinois
                    {"area_code": "312", "state": "IL", "city": "Chicago"},
                    # Georgia
                    {"area_code": "404", "state": "GA", "city": "Atlanta"},
                    # Texas
                    {"area_code": "512", "state": "TX", "city": "Austin"},
                    {"area_code": "713", "state": "TX", "city": "Houston"},
                    # Massachusetts
                    {"area_code": "617", "state": "MA", "city": "Boston"},
                    # Nevada
                    {"area_code": "702", "state": "NV", "city": "Las Vegas"},
                    # Florida
                    {"area_code": "786", "state": "FL", "city": "Miami"},
                    # North Carolina
                    {"area_code": "704", "state": "NC", "city": "Charlotte"},
                    {"area_code": "919", "state": "NC", "city": "Raleigh"},
                    {"area_code": "910", "state": "NC", "city": "Wilmington"},
                    {"area_code": "828", "state": "NC", "city": "Asheville"},
                    {"area_code": "336", "state": "NC", "city": "Greensboro"},
                    # Pennsylvania
                    {"area_code": "215", "state": "PA", "city": "Philadelphia"},
                    {"area_code": "267", "state": "PA", "city": "Philadelphia"},
                    {"area_code": "412", "state": "PA", "city": "Pittsburgh"},
                    {"area_code": "717", "state": "PA", "city": "Harrisburg"},
                    {"area_code": "610", "state": "PA", "city": "Allentown"},
                ]

        logger.info(
            f"Retrieved {len(area_codes)} area codes for {country}, user_id: {user_id}"
        )

        return {
            "success": True,
            "country": country,
            "area_codes": area_codes,
            "tier": tier_manager.get_user_tier(user_id),
        }

    except Exception as e:
        logger.error(
            f"Failed to get area codes for {country}, user_id: {user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve area code list")
