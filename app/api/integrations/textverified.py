"""TextVerified API endpoints for frontend integration."""
from app.core.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user_id

logger = get_logger(__name__)

router = APIRouter(prefix="/api/textverified", tags=["TextVerified"])


@router.get("/services")
async def get_textverified_services(
    user_id: str = Depends(get_current_user_id)
):
    """Get available services from TextVerified."""
    try:
        # TextVerified supports 100+ services
        # Return curated list of most popular services
        services = [
            {"id": "google", "name": "Google", "price": 0.50, "icon": "🔍"},
            {"id": "whatsapp", "name": "WhatsApp", "price": 0.75, "icon": "💬"},
            {"id": "telegram", "name": "Telegram", "price": 0.50, "icon": "✈️"},
            {"id": "discord", "name": "Discord", "price": 0.60, "icon": "🎮"},
            {"id": "instagram", "name": "Instagram", "price": 0.80, "icon": "📷"},
            {"id": "facebook", "name": "Facebook", "price": 0.75, "icon": "📘"},
            {"id": "twitter", "name": "Twitter/X", "price": 0.90, "icon": "🐦"},
            {"id": "tiktok", "name": "TikTok", "price": 0.85, "icon": "🎵"},
            {"id": "microsoft", "name": "Microsoft", "price": 0.60, "icon": "🪟"},
            {"id": "amazon", "name": "Amazon", "price": 0.70, "icon": "📦"},
            {"id": "uber", "name": "Uber", "price": 0.80, "icon": "🚗"},
            {"id": "netflix", "name": "Netflix", "price": 0.90, "icon": "🎬"},
            {"id": "spotify", "name": "Spotify", "price": 0.70, "icon": "🎵"},
            {"id": "paypal", "name": "PayPal", "price": 0.85, "icon": "💳"},
            {"id": "linkedin", "name": "LinkedIn", "price": 0.80, "icon": "💼"},
            {"id": "snapchat", "name": "Snapchat", "price": 0.75, "icon": "👻"},
            {"id": "yahoo", "name": "Yahoo", "price": 0.60, "icon": "📧"},
            {"id": "outlook", "name": "Outlook", "price": 0.60, "icon": "📨"},
            {"id": "apple", "name": "Apple", "price": 0.90, "icon": "🍎"},
            {"id": "samsung", "name": "Samsung", "price": 0.70, "icon": "📱"},
        ]

        return {
            "success": True,
            "services": services,
            "total": len(services),
            "provider": "textverified"
        }

    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load services")


@router.get("/countries")
async def get_textverified_countries(
    user_id: str = Depends(get_current_user_id)
):
    """Get available countries from TextVerified."""
    try:
        # TextVerified supports 190+ countries
        # Return most popular countries
        countries = [
            {"code": "US", "name": "United States", "flag": "🇺🇸", "available": True},
            {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧", "available": True},
            {"code": "CA", "name": "Canada", "flag": "🇨🇦", "available": True},
            {"code": "DE", "name": "Germany", "flag": "🇩🇪", "available": True},
            {"code": "FR", "name": "France", "flag": "🇫🇷", "available": True},
            {"code": "AU", "name": "Australia", "flag": "🇦🇺", "available": True},
            {"code": "IN", "name": "India", "flag": "🇮🇳", "available": True},
            {"code": "BR", "name": "Brazil", "flag": "🇧🇷", "available": True},
            {"code": "MX", "name": "Mexico", "flag": "🇲🇽", "available": True},
            {"code": "ES", "name": "Spain", "flag": "🇪🇸", "available": True},
            {"code": "IT", "name": "Italy", "flag": "🇮🇹", "available": True},
            {"code": "NL", "name": "Netherlands", "flag": "🇳🇱", "available": True},
            {"code": "SE", "name": "Sweden", "flag": "🇸🇪", "available": True},
            {"code": "PL", "name": "Poland", "flag": "🇵🇱", "available": True},
            {"code": "JP", "name": "Japan", "flag": "🇯🇵", "available": True},
            {"code": "KR", "name": "South Korea", "flag": "🇰🇷", "available": True},
            {"code": "SG", "name": "Singapore", "flag": "🇸🇬", "available": True},
            {"code": "AE", "name": "UAE", "flag": "🇦🇪", "available": True},
            {"code": "ZA", "name": "South Africa", "flag": "🇿🇦", "available": True},
            {"code": "NG", "name": "Nigeria", "flag": "🇳🇬", "available": True},
        ]

        return {
            "success": True,
            "countries": countries,
            "total": len(countries),
            "provider": "textverified"
        }

    except Exception as e:
        logger.error(f"Failed to get countries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load countries")


@router.get("/balance")
async def get_textverified_balance(
    user_id: str = Depends(get_current_user_id)
):
    """Get TextVerified account balance."""
    try:
        textverified = provider_manager.get_provider("textverified")
        balance_data = await textverified.get_balance()
        balance = balance_data.get("balance", 0.0)

        return {
            "success": True,
            "balance": balance,
            "provider": "textverified",
            "status": "active" if balance > 1.0 else "low"
        }

    except Exception as e:
        logger.warning(f"TextVerified balance check failed: {str(e)}")
        # Return success = False but don't raise exception
        # This allows the dashboard to load even if balance check fails
        return {
            "success": False,
            "balance": 0.0,
            "provider": "textverified",
            "status": "unavailable",
            "error": "Unable to check balance - API may be unavailable",
            "message": "Verification creation will still work if you have credits"
        }
