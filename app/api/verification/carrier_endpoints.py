"""Carrier/ISP filtering endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.unified_cache import cache
from app.models.carrier_analytics import CarrierAnalytics
from app.models.user import User
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.get("/carriers/{country}")
async def get_available_carriers(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get list of available carriers/ISPs with real success rates from analytics.

    Extracts carriers from past verifications and CarrierAnalytics data.
    
    IMPORTANT: Carrier selection is a PREFERENCE, not a guarantee.
    TextVerified will try to fulfill the preference but may return a different carrier.
    """
    logger.info(f"Carrier list requested by user_id: {user_id}, country: {country}")

    try:
        # Query real success rates from CarrierAnalytics
        analytics_query = db.query(
            CarrierAnalytics.requested_carrier,
            func.count(CarrierAnalytics.id).label("total"),
            func.sum(case((CarrierAnalytics.exact_match == True, 1), else_=0)).label("matches"),
        ).filter(
            CarrierAnalytics.outcome == "accepted"
        ).group_by(
            CarrierAnalytics.requested_carrier
        ).all()

        # Build carrier list with real success rates
        carriers = []
        for carrier_name, total, matches in analytics_query:
            success_rate = (matches / total * 100) if total > 0 else 90
            carriers.append(
                {
                    "id": carrier_name.lower().replace(" ", "_"),
                    "name": carrier_name.title(),
                    "success_rate": round(success_rate, 1),
                    "total_verifications": total,
                    "guarantee": False,
                    "type": "preference",
                }
            )

        # If no analytics data, use TextVerified's actual carrier options
        # (from TextVerified UI: AT&T, T-Mobile, Verizon only)
        if not carriers:
            carriers = [
                {
                    "id": "att",
                    "name": "AT&T",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
                {
                    "id": "tmobile",
                    "name": "T-Mobile",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
                {
                    "id": "verizon",
                    "name": "Verizon",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
            ]

        # Sort by success rate
        carriers.sort(key=lambda x: x["success_rate"], reverse=True)

        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        result = {
            "success": True,
            "country": country,
            "carriers": carriers,
            "tier": user_tier,
            "can_select": user_tier in ["payg", "pro", "custom"],
            "source": "analytics" if len(analytics_query) > 0 else "fallback",
            "note": "Carrier selection is a preference, not a guarantee. TextVerified will try to fulfill your preference but may return a different carrier.",
        }

        logger.info(
            f"Retrieved {len(carriers)} carriers from {'analytics' if len(analytics_query) > 0 else 'fallback'} for {country}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get carriers: {str(e)}", exc_info=True)

        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        return {
            "success": True,
            "country": country,
            "carriers": [
                {
                    "id": "att",
                    "name": "AT&T",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
                {
                    "id": "tmobile",
                    "name": "T-Mobile",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
                {
                    "id": "verizon",
                    "name": "Verizon",
                    "success_rate": 90,
                    "total_verifications": 0,
                    "guarantee": False,
                    "type": "preference",
                },
            ],
            "tier": user_tier,
            "can_select": user_tier in ["payg", "pro", "custom"],
            "source": "fallback",
            "note": "Carrier selection is a preference, not a guarantee. TextVerified will try to fulfill your preference but may return a different carrier.",
        }


@router.get("/area-codes/{country}")
async def get_available_area_codes(
    country: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get list of available area codes for a country with real-time data.

    Available to all authenticated users for viewing.
    Selection requires PAYG+ tier (enforced at purchase time).
    """
    logger.info(f"Area codes requested by user_id: {user_id}, country: {country}")

    # Static fallback area codes
    STATIC_FALLBACK_AREA_CODES = [
        {"area_code": "212", "state": "NY", "city": "New York City"},
        {"area_code": "917", "state": "NY", "city": "New York City"},
        {"area_code": "213", "state": "CA", "city": "Los Angeles"},
        {"area_code": "310", "state": "CA", "city": "Los Angeles"},
        {"area_code": "415", "state": "CA", "city": "San Francisco"},
        {"area_code": "312", "state": "IL", "city": "Chicago"},
        {"area_code": "404", "state": "GA", "city": "Atlanta"},
        {"area_code": "512", "state": "TX", "city": "Austin"},
        {"area_code": "713", "state": "TX", "city": "Houston"},
        {"area_code": "617", "state": "MA", "city": "Boston"},
        {"area_code": "702", "state": "NV", "city": "Las Vegas"},
        {"area_code": "786", "state": "FL", "city": "Miami"},
        {"area_code": "704", "state": "NC", "city": "Charlotte"},
        {"area_code": "919", "state": "NC", "city": "Raleigh"},
        {"area_code": "910", "state": "NC", "city": "Wilmington"},
        {"area_code": "828", "state": "NC", "city": "Asheville"},
        {"area_code": "336", "state": "NC", "city": "Greensboro"},
        {"area_code": "215", "state": "PA", "city": "Philadelphia"},
        {"area_code": "267", "state": "PA", "city": "Philadelphia"},
        {"area_code": "412", "state": "PA", "city": "Pittsburgh"},
    ]

    try:
        # Try to get from TextVerified API

        # Check cache first
        cache_key = f"area_codes_{country}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached area codes for {country}")
            return cached_data

        tv_service = TextVerifiedService()

        # Get area codes from TextVerified (DYNAMIC)
        logger.info("Calling TextVerified API for area codes: country=%s", country)
        codes = await tv_service.get_area_codes_list()

        if not codes:
            raise Exception("No area codes returned from API")

        # Enhance with city data from static map
        enhanced = []
        for code in codes:
            area_code_str = str(code.get("area_code", ""))
            city_data = next(
                (
                    ac
                    for ac in STATIC_FALLBACK_AREA_CODES
                    if ac["area_code"] == area_code_str
                ),
                {"city": "Unknown", "state": code.get("state", country.upper())},
            )
            enhanced.append(
                {
                    "area_code": area_code_str,
                    "city": city_data.get("city", "Unknown"),
                    "state": code.get("state")
                    or city_data.get("state", country.upper()),
                }
            )

        # Get user tier for response
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        result = {
            "success": True,
            "country": country,
            "area_codes": enhanced,
            "tier": user_tier,
            "can_select": user_tier in ["payg", "pro", "custom"],
            "source": "textverified_api",
        }

        # Cache for 5 minutes
        await cache.set(cache_key, result, ttl=300)

        logger.info(
            f"Retrieved {len(enhanced)} area codes from TextVerified API for {country}"
        )
        return result

    except Exception as e:
        logger.error(
            f"Failed to get area codes from TextVerified API: {str(e)}", exc_info=True
        )

        # FALLBACK to static list
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        return {
            "success": True,
            "country": country,
            "area_codes": STATIC_FALLBACK_AREA_CODES,
            "tier": user_tier,
            "can_select": user_tier in ["payg", "pro", "custom"],
            "source": "fallback",
        }
