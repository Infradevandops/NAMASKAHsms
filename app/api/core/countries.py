"""Countries API - Get supported countries for SMS verification"""
from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.core.unified_cache import cache

logger = get_logger(__name__)

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("/")
async def get_all_countries():
    """Get all countries - USA only (TextVerified supports USA only)"""
    return {
        "success": True,
        "countries": [
            {"code": "usa", "name": "United States", "prefix": "1"}
        ],
        "total": 1
    }


def get_flag_emoji(country_code: str) -> str:
    """Convert country code to flag emoji"""
    flag_map = {
        "russia": "🇷🇺", "india": "🇮🇳", "indonesia": "🇮🇩",
        "philippines": "🇵🇭", "vietnam": "🇻🇳", "china": "🇨🇳",
        "usa": "🇺🇸", "england": "🇬🇧", "canada": "🇨🇦",
        "germany": "🇩🇪", "france": "🇫🇷", "poland": "🇵🇱",
        "ukraine": "🇺🇦", "kazakhstan": "🇰🇿", "romania": "🇷🇴",
        "brazil": "🇧🇷", "mexico": "🇲🇽", "argentina": "🇦🇷",
        "thailand": "🇹🇭", "malaysia": "🇲🇾", "singapore": "🇸🇬",
        "hongkong": "🇭🇰", "japan": "🇯🇵", "southkorea": "🇰🇷",
        "australia": "🇦🇺", "turkey": "🇹🇷", "egypt": "🇪🇬",
        "nigeria": "🇳🇬", "southafrica": "🇿🇦", "spain": "🇪🇸",
        "italy": "🇮🇹", "netherlands": "🇳🇱", "belgium": "🇧🇪",
        "sweden": "🇸🇪", "norway": "🇳🇴", "denmark": "🇩🇰",
        "finland": "🇫🇮", "portugal": "🇵🇹", "greece": "🇬🇷",
        "czech": "🇨🇿", "austria": "🇦🇹", "switzerland": "🇨🇭",
        "israel": "🇮🇱", "uae": "🇦🇪", "saudi": "🇸🇦",
        "pakistan": "🇵🇰", "bangladesh": "🇧🇩", "srilanka": "🇱🇰",
        "myanmar": "🇲🇲", "cambodia": "🇰🇭", "laos": "🇱🇦",
        "nepal": "🇳🇵", "taiwan": "🇹🇼"
    }
    return flag_map.get(country_code.lower(), "🌍")


def get_fallback_countries():
    """Fallback country list if API fails - all 37 countries"""
    return {
        "success": True,
        "countries": [
            # North America
            {"code": "usa", "name": "United States", "prefix": "1", "flag": "🇺🇸"},
            {"code": "canada", "name": "Canada", "prefix": "1", "flag": "🇨🇦"},
            {"code": "mexico", "name": "Mexico", "prefix": "52", "flag": "🇲🇽"},
            # Europe
            {"code": "uk", "name": "United Kingdom", "prefix": "44", "flag": "🇬🇧"},
            {"code": "germany", "name": "Germany", "prefix": "49", "flag": "🇩🇪"},
            {"code": "france", "name": "France", "prefix": "33", "flag": "🇫🇷"},
            {"code": "italy", "name": "Italy", "prefix": "39", "flag": "🇮🇹"},
            {"code": "spain", "name": "Spain", "prefix": "34", "flag": "🇪🇸"},
            {"code": "netherlands", "name": "Netherlands", "prefix": "31", "flag": "🇳🇱"},
            {"code": "poland", "name": "Poland", "prefix": "48", "flag": "🇵🇱"},
            {"code": "russia", "name": "Russia", "prefix": "7", "flag": "🇷🇺"},
            {"code": "ukraine", "name": "Ukraine", "prefix": "380", "flag": "🇺🇦"},
            {"code": "sweden", "name": "Sweden", "prefix": "46", "flag": "🇸🇪"},
            {"code": "norway", "name": "Norway", "prefix": "47", "flag": "🇳🇴"},
            {"code": "finland", "name": "Finland", "prefix": "358", "flag": "🇫🇮"},
            # Asia
            {"code": "india", "name": "India", "prefix": "91", "flag": "🇮🇳"},
            {"code": "china", "name": "China", "prefix": "86", "flag": "🇨🇳"},
            {"code": "japan", "name": "Japan", "prefix": "81", "flag": "🇯🇵"},
            {"code": "south_korea", "name": "South Korea", "prefix": "82", "flag": "🇰🇷"},
            {"code": "singapore", "name": "Singapore", "prefix": "65", "flag": "🇸🇬"},
            {"code": "thailand", "name": "Thailand", "prefix": "66", "flag": "🇹🇭"},
            {"code": "vietnam", "name": "Vietnam", "prefix": "84", "flag": "🇻🇳"},
            {"code": "philippines", "name": "Philippines", "prefix": "63", "flag": "🇵🇭"},
            {"code": "indonesia", "name": "Indonesia", "prefix": "62", "flag": "🇮🇩"},
            {"code": "malaysia", "name": "Malaysia", "prefix": "60", "flag": "🇲🇾"},
            # Oceania
            {"code": "australia", "name": "Australia", "prefix": "61", "flag": "🇦🇺"},
            {"code": "new_zealand", "name": "New Zealand", "prefix": "64", "flag": "🇳🇿"},
            # South America
            {"code": "brazil", "name": "Brazil", "prefix": "55", "flag": "🇧🇷"},
            {"code": "argentina", "name": "Argentina", "prefix": "54", "flag": "🇦🇷"},
            {"code": "chile", "name": "Chile", "prefix": "56", "flag": "🇨🇱"},
            {"code": "colombia", "name": "Colombia", "prefix": "57", "flag": "🇨🇴"},
            # Africa
            {"code": "south_africa", "name": "South Africa", "prefix": "27", "flag": "🇿🇦"},
            {"code": "nigeria", "name": "Nigeria", "prefix": "234", "flag": "🇳🇬"},
            {"code": "egypt", "name": "Egypt", "prefix": "20", "flag": "🇪🇬"},
            # Middle East
            {"code": "israel", "name": "Israel", "prefix": "972", "flag": "🇮🇱"},
            {"code": "uae", "name": "United Arab Emirates", "prefix": "971", "flag": "🇦🇪"},
            {"code": "saudi_arabia", "name": "Saudi Arabia", "prefix": "966", "flag": "🇸🇦"},
        ],
        "total": 37,
        "note": "Fallback list - API unavailable"
    }


@router.get("/usa/area-codes")
async def get_usa_area_codes():
    """Get all US area codes from TextVerified API (cached 5min for fresh data)"""
    try:
        # Check cache first (version 2 with correct field names)
        cache_key_str = cache.cache_key("usa", "area_codes", "v2")
        cached_result = await cache.get(cache_key_str)
        if cached_result:
            return cached_result

        from app.services.textverified_integration import get_textverified_integration
        integration = get_textverified_integration()
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
                
            area_codes.append({
                "code": str(area_code),
                "name": str(name),
                "country": "US",
                "available": code_data.get("available", True)
            })

        result = {
            "success": True,
            "country": "United States",
            "area_codes": area_codes,
            "total": len(area_codes)
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
            {"id": "any", "name": "Any Carrier"}
        ]

        return {
            "success": True,
            "carriers": carriers,
            "total": len(carriers)
        }
    except Exception as e:
        logger.error(f"Failed to get carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load carriers")


@router.get("/{country}/services")
async def get_country_services(country: str):
    """Get available services for USA from TextVerified API"""
    if country.lower() != "usa":
        raise HTTPException(status_code=404, detail="Only USA is supported")

    cache_key_str = cache.cache_key("usa_services_v3")
    cached_result = await cache.get(cache_key_str)
    if cached_result:
        return cached_result

    try:
        from app.services.textverified_integration import get_textverified_integration
        integration = get_textverified_integration()
        services = await integration.get_services_list(force_refresh=True)

        result = {
            "success": True,
            "country": "United States",
            "services": services,
            "total": len(services)
        }

        await cache.set(cache_key_str, result, ttl=3600)
        return result

    except Exception as e:
        logger.error(f"Failed to get services from TextVerified: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load services")
