"""Services endpoint for verification system.

PUBLIC endpoint — no auth required. Service list is not user-specific.
Auth header is accepted but ignored. CSRF middleware whitelists /api/countries.
"""

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()

# Fallback services (always available) — 84 services
FALLBACK_SERVICES = [
    # Top messaging & social (10)
    {"id": "whatsapp", "name": "WhatsApp", "price": 2.50},
    {"id": "telegram", "name": "Telegram", "price": 2.00},
    {"id": "discord", "name": "Discord", "price": 2.25},
    {"id": "instagram", "name": "Instagram", "price": 2.75},
    {"id": "facebook", "name": "Facebook", "price": 2.50},
    {"id": "google", "name": "Google", "price": 2.00},
    {"id": "twitter", "name": "Twitter", "price": 2.50},
    {"id": "microsoft", "name": "Microsoft", "price": 2.25},
    {"id": "amazon", "name": "Amazon", "price": 2.50},
    {"id": "uber", "name": "Uber", "price": 2.75},
    
    # Tech & platforms (10)
    {"id": "apple", "name": "Apple", "price": 2.50},
    {"id": "tiktok", "name": "TikTok", "price": 2.75},
    {"id": "snapchat", "name": "Snapchat", "price": 2.50},
    {"id": "linkedin", "name": "LinkedIn", "price": 2.75},
    {"id": "netflix", "name": "Netflix", "price": 2.00},
    {"id": "spotify", "name": "Spotify", "price": 2.00},
    {"id": "reddit", "name": "Reddit", "price": 2.00},
    {"id": "pinterest", "name": "Pinterest", "price": 2.00},
    {"id": "tumblr", "name": "Tumblr", "price": 2.00},
    {"id": "twitch", "name": "Twitch", "price": 2.50},
    
    # Finance & payments (10)
    {"id": "paypal", "name": "PayPal", "price": 2.50},
    {"id": "venmo", "name": "Venmo", "price": 0.50},
    {"id": "cashapp", "name": "Cash App", "price": 2.50},
    {"id": "coinbase", "name": "Coinbase", "price": 2.75},
    {"id": "binance", "name": "Binance", "price": 2.75},
    {"id": "robinhood", "name": "Robinhood", "price": 2.50},
    {"id": "stripe", "name": "Stripe", "price": 2.50},
    {"id": "square", "name": "Square", "price": 2.50},
    {"id": "chime", "name": "Chime", "price": 2.50},
    {"id": "revolut", "name": "Revolut", "price": 2.50},
    
    # E-commerce & retail (10)
    {"id": "walmart", "name": "Walmart", "price": 0.50},
    {"id": "target", "name": "Target", "price": 0.50},
    {"id": "ebay", "name": "eBay", "price": 2.00},
    {"id": "etsy", "name": "Etsy", "price": 2.00},
    {"id": "shopify", "name": "Shopify", "price": 2.50},
    {"id": "alibaba", "name": "Alibaba", "price": 2.50},
    {"id": "aliexpress", "name": "AliExpress", "price": 2.50},
    {"id": "wish", "name": "Wish", "price": 2.00},
    {"id": "mercari", "name": "Mercari", "price": 2.00},
    {"id": "poshmark", "name": "Poshmark", "price": 2.00},
    
    # Food & delivery (10)
    {"id": "doordash", "name": "DoorDash", "price": 2.50},
    {"id": "ubereats", "name": "Uber Eats", "price": 2.75},
    {"id": "grubhub", "name": "Grubhub", "price": 2.50},
    {"id": "postmates", "name": "Postmates", "price": 2.50},
    {"id": "instacart", "name": "Instacart", "price": 2.50},
    {"id": "seamless", "name": "Seamless", "price": 2.50},
    {"id": "deliveroo", "name": "Deliveroo", "price": 2.50},
    {"id": "justeat", "name": "Just Eat", "price": 2.50},
    {"id": "zomato", "name": "Zomato", "price": 2.50},
    {"id": "swiggy", "name": "Swiggy", "price": 2.50},
    
    # Travel & transport (10)
    {"id": "airbnb", "name": "Airbnb", "price": 2.75},
    {"id": "booking", "name": "Booking.com", "price": 2.50},
    {"id": "expedia", "name": "Expedia", "price": 2.50},
    {"id": "lyft", "name": "Lyft", "price": 2.75},
    {"id": "vrbo", "name": "VRBO", "price": 2.50},
    {"id": "tripadvisor", "name": "TripAdvisor", "price": 2.50},
    {"id": "kayak", "name": "Kayak", "price": 2.50},
    {"id": "hopper", "name": "Hopper", "price": 2.50},
    {"id": "skyscanner", "name": "Skyscanner", "price": 2.50},
    {"id": "hotels", "name": "Hotels.com", "price": 2.50},
    
    # Dating & social (8)
    {"id": "tinder", "name": "Tinder", "price": 2.50},
    {"id": "bumble", "name": "Bumble", "price": 2.50},
    {"id": "hinge", "name": "Hinge", "price": 2.50},
    {"id": "match", "name": "Match.com", "price": 0.50},
    {"id": "pof", "name": "Plenty of Fish", "price": 2.00},
    {"id": "okcupid", "name": "OkCupid", "price": 2.00},
    {"id": "grindr", "name": "Grindr", "price": 2.50},
    {"id": "meetme", "name": "MeetMe", "price": 2.00},
    
    # Gaming (8)
    {"id": "steam", "name": "Steam", "price": 2.50},
    {"id": "epicgames", "name": "Epic Games", "price": 2.50},
    {"id": "playstation", "name": "PlayStation", "price": 2.50},
    {"id": "xbox", "name": "Xbox", "price": 2.50},
    {"id": "nintendo", "name": "Nintendo", "price": 2.50},
    {"id": "roblox", "name": "Roblox", "price": 2.50},
    {"id": "fortnite", "name": "Fortnite", "price": 2.50},
    {"id": "valorant", "name": "Valorant", "price": 2.50},
    
    # Communication (8)
    {"id": "zoom", "name": "Zoom", "price": 2.00},
    {"id": "slack", "name": "Slack", "price": 2.50},
    {"id": "teams", "name": "Microsoft Teams", "price": 2.25},
    {"id": "skype", "name": "Skype", "price": 2.00},
    {"id": "viber", "name": "Viber", "price": 2.00},
    {"id": "wechat", "name": "WeChat", "price": 2.50},
    {"id": "line", "name": "LINE", "price": 2.50},
    {"id": "kakao", "name": "KakaoTalk", "price": 2.50},
]


@router.get("/{country}/services")
async def get_services(country: str):
    """Get services with fallback on error."""
    settings = get_settings()

    try:
        # Try to get from API
        raw = await _tv.get_services_list()

        if not raw:
            logger.warning(f"Empty services list for {country}, using fallback")
            raw = FALLBACK_SERVICES

        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in raw
            ],
            "total": len(raw),
            "source": "api",
        }

    except Exception as e:
        logger.error(f"Failed to get services for {country}: {str(e)}", exc_info=True)

        # Return fallback services
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in FALLBACK_SERVICES
            ],
            "total": len(FALLBACK_SERVICES),
            "source": "fallback",
            "error": "API unavailable, using cached services",
        }


@router.get("/{country}/services/batch-pricing")
async def get_services_batch_pricing(country: str):
    """Return services with accurate pricing from 24h cache. Warms cache if cold."""
    settings = get_settings()

    try:
        # Try cache first
        cached = await cache.get("tv:services_list")
        if cached:
            return {
                "services": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "price": round(s["price"] * settings.price_markup, 2),
                        "cost": round(s["price"] * settings.price_markup, 2),
                    }
                    for s in cached
                ],
                "total": len(cached),
                "source": "cache",
            }

        # Cache cold — try API
        raw = await _tv.get_services_list()

        if not raw:
            logger.warning(f"Empty services list for {country}, using fallback")
            raw = FALLBACK_SERVICES

        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in raw
            ],
            "total": len(raw),
            "source": "warming",
        }

    except Exception as e:
        logger.error(
            f"Failed to get batch pricing for {country}: {str(e)}", exc_info=True
        )

        # Return fallback
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in FALLBACK_SERVICES
            ],
            "total": len(FALLBACK_SERVICES),
            "source": "fallback",
            "error": "API unavailable, using cached services",
        }
