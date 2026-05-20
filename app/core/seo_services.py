"""
SEO service page config.

Base metadata (slug, icon) is defined once at module level.
Live price is merged from the TextVerified Redis cache at render time.
"""

from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level constant — loaded once at import, never rebuilt per request.
# Keys match TextVerified service_name (lowercase).
SEO_SERVICES: Dict[str, dict] = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬"},
    "telegram": {"name": "Telegram", "icon": "✈️"},
    "google": {"name": "Google", "icon": "🔍"},
    "discord": {"name": "Discord", "icon": "🎮"},
    "facebook": {"name": "Facebook", "icon": "👤"},
    "instagram": {"name": "Instagram", "icon": "📸"},
    "twitter": {"name": "Twitter", "icon": "🐦"},
    "tiktok": {"name": "TikTok", "icon": "🎵"},
    "uber": {"name": "Uber", "icon": "🚗"},
    "amazon": {"name": "Amazon", "icon": "📦"},
    "netflix": {"name": "Netflix", "icon": "🎬"},
    "paypal": {"name": "PayPal", "icon": "💳"},
    "snapchat": {"name": "Snapchat", "icon": "👻"},
    "linkedin": {"name": "LinkedIn", "icon": "💼"},
    "microsoft": {"name": "Microsoft", "icon": "🪟"},
    "apple": {"name": "Apple", "icon": "🍎"},
    "coinbase": {"name": "Coinbase", "icon": "₿"},
    "binance": {"name": "Binance", "icon": "📈"},
    "airbnb": {"name": "Airbnb", "icon": "🏠"},
    "doordash": {"name": "DoorDash", "icon": "🍕"},
    "signal": {"name": "Signal", "icon": "🔒"},
    "viber": {"name": "Viber", "icon": "📞"},
    "line": {"name": "Line", "icon": "💚"},
    "wechat": {"name": "WeChat", "icon": "💬"},
    "steam": {"name": "Steam", "icon": "🎮"},
    "github": {"name": "GitHub", "icon": "🐙"},
    "aws": {"name": "AWS", "icon": "☁️"},
    "kraken": {"name": "Kraken", "icon": "🐙"},
    "cashapp": {"name": "Cash App", "icon": "💵"},
}

# Fallback price shown if cache is cold (TextVerified not yet polled)
_FALLBACK_PRICE = 2.63


async def get_service_for_page(slug: str) -> Optional[dict]:
    """
    Return service data for a SEO page.

    Merges static base config with live price from the TextVerified
    Redis cache (key: tv:services_list). No API call is made here.
    """
    base = SEO_SERVICES.get(slug)
    if not base:
        return None

    price = await _get_live_price(slug)

    return {
        "slug": slug,
        "name": base["name"],
        "icon": base["icon"],
        "price": price,
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
