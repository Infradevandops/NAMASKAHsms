"""Countries API - Get supported countries for SMS verification"""


from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("/")
async def get_all_countries():
    """Get all supported countries - Currently US only (TextVerified limitation)."""
    return {
        "success": True,
        "countries": [
            {"code": "usa", "name": "United States", "prefix": "1", "flag": "🇺🇸"},
        ],
        "total": 1,
        "note": "Only US supported - awaiting additional provider integrations",
    }


def get_flag_emoji(country_code: str) -> str:

    """Convert country code to flag emoji"""
    flag_map = {
        "russia": "🇷🇺",
        "india": "🇮🇳",
        "indonesia": "🇮🇩",
        "philippines": "🇵🇭",
        "vietnam": "🇻🇳",
        "china": "🇨🇳",
        "usa": "🇺🇸",
        "england": "🇬🇧",
        "canada": "🇨🇦",
        "germany": "🇩🇪",
        "france": "🇫🇷",
        "poland": "🇵🇱",
        "ukraine": "🇺🇦",
        "kazakhstan": "🇰🇿",
        "romania": "🇷🇴",
        "brazil": "🇧🇷",
        "mexico": "🇲🇽",
        "argentina": "🇦🇷",
        "thailand": "🇹🇭",
        "malaysia": "🇲🇾",
        "singapore": "🇸🇬",
        "hongkong": "🇭🇰",
        "japan": "🇯🇵",
        "southkorea": "🇰🇷",
        "australia": "🇦🇺",
        "turkey": "🇹🇷",
        "egypt": "🇪🇬",
        "nigeria": "🇳🇬",
        "southafrica": "🇿🇦",
        "spain": "🇪🇸",
        "italy": "🇮🇹",
        "netherlands": "🇳🇱",
        "belgium": "🇧🇪",
        "sweden": "🇸🇪",
        "norway": "🇳🇴",
        "denmark": "🇩🇰",
        "finland": "🇫🇮",
        "portugal": "🇵🇹",
        "greece": "🇬🇷",
        "czech": "🇨🇿",
        "austria": "🇦🇹",
        "switzerland": "🇨🇭",
        "israel": "🇮🇱",
        "uae": "🇦🇪",
        "saudi": "🇸🇦",
        "pakistan": "🇵🇰",
        "bangladesh": "🇧🇩",
        "srilanka": "🇱🇰",
        "myanmar": "🇲🇲",
        "cambodia": "🇰🇭",
        "laos": "🇱🇦",
        "nepal": "🇳🇵",
        "taiwan": "🇹🇼",
    }
    return flag_map.get(country_code.lower(), "🌍")


@router.get("/usa/area-codes")
async def get_usa_area_codes():
    """Get all US area codes from TextVerified API (cached 5min for fresh data)"""
try:
        # Check cache first (version 2 with correct field names)
        cache_key_str = cache.cache_key("usa", "area_codes", "v2")
        cached_result = await cache.get(cache_key_str)
if cached_result:
            return cached_result


        integration = TextVerifiedService()
        raw_codes = await integration.get_area_codes_list()

        # Transform to frontend-expected format
        area_codes = []
for code_data in raw_codes:
            # Extract code and name (handle different possible fields)
            area_code = code_data.get("code") or code_data.get("area_code")
            name = code_data.get("name") or code_data.get("region") or code_data.get("state")

            # Skip if code or name is missing/null
if not area_code or not name:
                continue

            area_codes.append(
                {
                    "code": str(area_code),
                    "name": str(name),
                    "country": "US",
                    "available": code_data.get("available", True),
                }
            )

        result = {
            "success": True,
            "country": "United States",
            "area_codes": area_codes,
            "total": len(area_codes),
        }

        # Cache for 5 minutes (300 seconds) for fresh availability
        await cache.set(cache_key_str, result, ttl=300)
        return result

except Exception as e:
        logger.error(f"Failed to get area codes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load area codes")


@router.get("/usa/carriers")
async def get_usa_carriers():
    """Get available US carriers"""
try:
        carriers = [
            {"id": "verizon", "name": "Verizon"},
            {"id": "att", "name": "AT&T"},
            {"id": "tmobile", "name": "T-Mobile"},
            {"id": "sprint", "name": "Sprint"},
            {"id": "us_cellular", "name": "US Cellular"},
            {"id": "any", "name": "Any Carrier"},
        ]

        return {"success": True, "carriers": carriers, "total": len(carriers)}
except Exception as e:
        logger.error(f"Failed to get carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load carriers")


@router.get("/{country}/services")
async def get_country_services(country: str):
    """Get available services for a specific country from TextVerified API"""
    # International support enabled for all countries in fallback list
    country_code = country.lower()
    cache_key_str = cache.cache_key(f"services_v3_{country_code}")

    cached_result = await cache.get(cache_key_str)
if cached_result:
        return cached_result

try:

        integration = TextVerifiedService()
        # Fetch services specific to the requested country
        services = await integration.get_services_list(country=country_code, force_refresh=True)

        result = {
            "success": True,
            "country": country.upper(),
            "services": services,
            "total": len(services),
        }

        # Cache for 1 hour (3600 seconds)
        await cache.set(cache_key_str, result, ttl=3600)
        return result

except Exception as e:
        logger.error(f"Failed to get services from TextVerified for {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load services for {country}")