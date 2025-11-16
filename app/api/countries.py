"""Countries API - Get supported countries for SMS verification"""
from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService
from app.core.cache import cache

logger = get_logger(__name__)

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("/")
async def get_all_countries():
    """Get all countries supported for SMS verification"""
    try:
        # Return fallback list (TextVerified is available in 180+ countries)
        return get_fallback_countries()
        
    except Exception as e:
        logger.error(f"Failed to get countries: {str(e)}")
        # Return fallback list
        return get_fallback_countries()


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
    """Fallback country list if API fails"""
    return {
        "success": True,
        "countries": [
            {"code": "russia", "name": "Russia", "prefix": "7", "flag": "🇷🇺"},
            {"code": "india", "name": "India", "prefix": "91", "flag": "🇮🇳"},
            {"code": "indonesia", "name": "Indonesia", "prefix": "62", "flag": "🇮🇩"},
            {"code": "philippines", "name": "Philippines", "prefix": "63", "flag": "🇵🇭"},
            {"code": "vietnam", "name": "Vietnam", "prefix": "84", "flag": "🇻🇳"},
            {"code": "china", "name": "China", "prefix": "86", "flag": "🇨🇳"},
            {"code": "usa", "name": "United States", "prefix": "1", "flag": "🇺🇸"},
            {"code": "england", "name": "United Kingdom", "prefix": "44", "flag": "🇬🇧"},
            {"code": "canada", "name": "Canada", "prefix": "1", "flag": "🇨🇦"},
            {"code": "germany", "name": "Germany", "prefix": "49", "flag": "🇩🇪"},
        ],
        "total": 10,
        "note": "Fallback list - API unavailable"
    }


@router.get("/{country}/services")
async def get_country_services(country: str):
    """Get available services for SMS verification in a specific country"""
    try:
        # TextVerified provides SMS verification service
        services = [
            {
                "id": "telegram",
                "name": "Telegram",
                "cost": 2.00,
                "available": 100
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp", 
                "cost": 2.50,
                "available": 50
            },
            {
                "id": "google",
                "name": "Google",
                "cost": 1.50,
                "available": 75
            }
        ]
        
        return {
            "success": True,
            "country": country,
            "services": services,
            "total": len(services)
        }
        
    except Exception as e:
        logger.error(f"Failed to get services for {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load services: {str(e)}")
