"""
SEO service page config.

Base metadata (slug, icon, country_count) is defined once at module level.
Live price is merged from the TextVerified Redis cache at render time —
so the page always shows the current price without an API call per request.
"""

from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level constant — loaded once at import, never rebuilt per request.
# Keys match TextVerified service_name (lowercase).
SEO_SERVICES: Dict[str, dict] = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "country_count": 47},
    "telegram": {"name": "Telegram", "icon": "✈️", "country_count": 45},
    "google": {"name": "Google", "icon": "🔍", "country_count": 50},
    "discord": {"name": "Discord", "icon": "🎮", "country_count": 40},
    "facebook": {"name": "Facebook", "icon": "👤", "country_count": 45},
    "instagram": {"name": "Instagram", "icon": "📸", "country_count": 45},
    "twitter": {"name": "Twitter", "icon": "🐦", "country_count": 40},
    "tiktok": {"name": "TikTok", "icon": "🎵", "country_count": 35},
    "uber": {"name": "Uber", "icon": "🚗", "country_count": 30},
    "amazon": {"name": "Amazon", "icon": "📦", "country_count": 40},
    "netflix": {"name": "Netflix", "icon": "🎬", "country_count": 35},
    "paypal": {"name": "PayPal", "icon": "💳", "country_count": 40},
    "snapchat": {"name": "Snapchat", "icon": "👻", "country_count": 30},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "country_count": 35},
    "microsoft": {"name": "Microsoft", "icon": "🪟", "country_count": 40},
    "apple": {"name": "Apple", "icon": "🍎", "country_count": 35},
    "coinbase": {"name": "Coinbase", "icon": "₿", "country_count": 25},
    "binance": {"name": "Binance", "icon": "📈", "country_count": 30},
    "airbnb": {"name": "Airbnb", "icon": "🏠", "country_count": 30},
    "doordash": {"name": "DoorDash", "icon": "🍕", "country_count": 5},
}

# Fallback price shown if cache is cold (TextVerified not yet polled)
_FALLBACK_PRICE = 2.63


async def get_service_for_page(slug: str) -> Optional[dict]:
    """
    Return service data for a SEO page.

    Merges static base config with live price from the TextVerified
    Redis cache (key: tv:services_list). No API call is made here —
    the cache is populated by the existing TextVerifiedService on first
    dashboard load or startup warm-up.
    """
    base = SEO_SERVICES.get(slug)
    if not base:
        return None

    price = await _get_live_price(slug)

    return {
        "slug": slug,
        "name": base["name"],
        "icon": base["icon"],
        "country_count": base["country_count"],
        "price": price,
        "countries": _default_countries(price),
    }


async def _get_live_price(slug: str) -> float:
    """Read price from the TextVerified Redis cache. Falls back to _FALLBACK_PRICE."""
    try:
        from app.core.unified_cache import cache

        cached: Optional[List] = await cache.get("tv:services_list")
        if cached:
            for svc in cached:
                if svc.get("id", "").lower() == slug and svc.get("price"):
                    return round(float(svc["price"]), 2)
    except Exception as e:
        logger.debug(f"SEO price cache miss for {slug}: {e}")

    return _FALLBACK_PRICE


def _default_countries(price: float) -> List[dict]:
    """Return a default country pricing table using the live price."""
    return [
        {"flag": "🇺🇸", "name": "USA", "price": price, "success_rate": 95},
        {"flag": "🇬🇧", "name": "UK", "price": price, "success_rate": 93},
        {"flag": "🇨🇦", "name": "Canada", "price": price, "success_rate": 92},
        {"flag": "🇮🇳", "name": "India", "price": price, "success_rate": 90},
        {"flag": "🇩🇪", "name": "Germany", "price": price, "success_rate": 91},
    ]
