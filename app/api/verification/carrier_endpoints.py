"""Carrier/ISP filtering endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.get("/carriers/{country}")
async def get_available_carriers(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get list of available carriers/ISPs for a country.

    Available to all authenticated users for viewing.
    Selection requires PRO+ tier (enforced at purchase time).
    """
    logger.info(f"Carrier list requested by user_id: {user_id}, country: {country}")

    try:
        # Fallback carrier list for US
        carriers = [
            {"id": "verizon", "name": "Verizon", "success_rate": 95},
            {"id": "att", "name": "AT&T", "success_rate": 93},
            {"id": "tmobile", "name": "T-Mobile", "success_rate": 92},
            {"id": "sprint", "name": "Sprint", "success_rate": 88},
            {"id": "us_cellular", "name": "US Cellular", "success_rate": 87},
        ]

        # Get user tier for response
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        logger.info(
            f"Retrieved {len(carriers)} carriers for {country}, user_id: {user_id}, tier: {user_tier}"
        )

        return {
            "success": True,
            "country": country,
            "carriers": carriers,
            "tier": user_tier,
            "can_select": user_tier in ["pro", "custom"],
        }

    except Exception as e:
        logger.error(
            f"Failed to get carriers for {country}, user_id: {user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve carrier list")


@router.get("/area-codes/{country}")
async def get_available_area_codes(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get list of available area codes for a country.

    Available to all authenticated users for viewing.
    Selection requires PAYG+ tier (enforced at purchase time).
    """
    logger.info(f"Area codes requested by user_id: {user_id}, country: {country}")

    try:
        area_codes = []

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

        # Get user tier for response
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.tier if user else "freemium"

        logger.info(
            f"Retrieved {len(area_codes)} area codes for {country}, user_id: {user_id}"
        )

        return {
            "success": True,
            "country": country,
            "area_codes": area_codes,
            "tier": user_tier,
            "can_select": user_tier in ["payg", "pro", "custom"],
        }

    except Exception as e:
        logger.error(
            f"Failed to get area codes for {country}, user_id: {user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve area code list")
