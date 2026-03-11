"""Services endpoint for verification system.

PUBLIC endpoint — no auth required. Service list is not user-specific.
Auth header is accepted but ignored. CSRF middleware whitelists /api/countries.
"""

from fastapi import APIRouter
import logging

from app.core.config import get_settings
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()

# Fallback services (always available)
FALLBACK_SERVICES = [
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
            "source": "api"
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
            "error": "API unavailable, using cached services"
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
        logger.error(f"Failed to get batch pricing for {country}: {str(e)}", exc_info=True)

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
            "error": "API unavailable, using cached services"
        }
