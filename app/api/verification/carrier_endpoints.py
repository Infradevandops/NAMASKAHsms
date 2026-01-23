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
    """Get list of available carriers/ISPs for a country with real-time data.

    Available to all authenticated users for viewing.
    Selection requires PRO+ tier (enforced at purchase time).
    """
    logger.info(f"Carrier list requested by user_id: {user_id}, country: {country}")

    # Static fallback carriers
    STATIC_FALLBACK_CARRIERS = [
        {"id": "verizon", "name": "Verizon", "success_rate": 95},
        {"id": "att", "name": "AT&T", "success_rate": 93},
        {"id": "tmobile", "name": "T-Mobile", "success_rate": 92},
        {"id": "sprint", "name": "Sprint", "success_rate": 88},
        {"id": "us_cellular", "name": "US Cellular", "success_rate": 87},
    ]

    try:
        # Try to get from TextVerified API
        from app.services.textverified_service import TextVerifiedService
        from app.services.availability_service import AvailabilityService
        from app.core.unified_cache import cache

        # Check cache first
        cache_key = f"carriers_{country}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached carriers for {country}")
            return cached_data

        tv_service = TextVerifiedService()
        availability_service = AvailabilityService(db)

        # Get carriers from TextVerified (DYNAMIC)
        carriers = await tv_service.get_available_carriers(country)

        if not carriers:
            raise Exception("No carriers returned from API")

        # Enhance with YOUR success rates (REAL DATA)
        enhanced_carriers = []
        for carrier in carriers:
            stats = availability_service.get_carrier_availability(
                carrier["name"], country
            )
            enhanced_carriers.append(
                {
                    "id": carrier.get("id", carrier["name"].lower().replace(" ", "_")),
                    "name": carrier["name"],
                    "success_rate": stats.get("success_rate", carrier.get("success_rate", 90)),
                    "total_verifications": stats.get("total", 0),
                }
            )

        # Sort by success rate (highest first)
        enhanced_carriers.sort(key=lambda x: x["success_rate"], reverse=True)

        # Get user tier for response
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        result = {
            "success": True,
            "country": country,
            "carriers": enhanced_carriers,
            "tier": user_tier,
            "can_select": user_tier in ["pro", "custom"],
            "source": "textverified_api",
        }

        # Cache for 5 minutes
        await cache.set(cache_key, result, ttl=300)

        logger.info(
            f"Retrieved {len(enhanced_carriers)} carriers from TextVerified API for {country}"
        )
        return result

    except Exception as e:
        logger.error(
            f"Failed to get carriers from TextVerified API: {str(e)}, using fallback"
        )

        # FALLBACK to static list
        user = db.query(User).filter(User.id == user_id).first()
        user_tier = user.subscription_tier if user else "freemium"

        return {
            "success": True,
            "country": country,
            "carriers": STATIC_FALLBACK_CARRIERS,
            "tier": user_tier,
            "can_select": user_tier in ["pro", "custom"],
            "source": "fallback",
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
        from app.services.textverified_service import TextVerifiedService
        from app.services.availability_service import AvailabilityService
        from app.core.unified_cache import cache

        # Check cache first
        cache_key = f"area_codes_{country}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached area codes for {country}")
            return cached_data

        tv_service = TextVerifiedService()
        availability_service = AvailabilityService(db)

        # Get area codes from TextVerified (DYNAMIC)
        logger.info(f"Calling TextVerified API for area codes: country={country}")
        codes = await tv_service.get_area_codes(country, service="telegram")
        
        logger.info(f"TextVerified API returned: {type(codes)}, length={len(codes) if codes else 0}")
        if codes:
            logger.info(f"First code sample: {codes[0] if len(codes) > 0 else 'none'}")

        if not codes or len(codes) == 0:
            logger.error(f"TextVerified API returned empty or None for area codes")
            raise Exception(f"No area codes returned from API (got {type(codes)}, len={len(codes) if codes else 0})")

        # Enhance with city/state data and success rates
        enhanced = []
        for code in codes:
            area_code_str = str(code.get("area_code", ""))
            
            # Try to find city/state from static map
            city_data = next(
                (ac for ac in STATIC_FALLBACK_AREA_CODES if ac["area_code"] == area_code_str),
                {"city": "Unknown", "state": country.upper()}
            )
            
            # Get success rate from your data
            try:
                stats = availability_service.get_area_code_availability(
                    area_code_str, country
                )
                success_rate = stats.get("success_rate", 90)
            except Exception as stats_error:
                logger.warning(f"Failed to get stats for area code {area_code_str}: {stats_error}")
                success_rate = 90
            
            enhanced.append({
                "area_code": area_code_str,
                "city": city_data.get("city", "Unknown"),
                "state": city_data.get("state", country.upper()),
                "available_count": code.get("available_count", 10),
                "success_rate": success_rate,
            })

        # Sort by success rate (highest first)
        enhanced.sort(key=lambda x: x["success_rate"], reverse=True)

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
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Full traceback will be in logs")

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
