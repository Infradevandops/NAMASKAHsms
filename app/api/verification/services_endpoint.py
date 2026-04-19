"""Services endpoint for verification system.

PUBLIC endpoint — no auth required. Service list is not user-specific.
Auth header is accepted but ignored. CSRF middleware whitelists /api/countries.

Pricing model:
  provider_price × markup = platform_price (what user sees and pays)
  If provider_price is null, the service is listed but not purchasable.
"""

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/countries", tags=["Services"])
_tv = TextVerifiedService()


def _apply_markup(provider_price, markup: float):
    """provider_price × markup, or None if provider_price is missing."""
    if provider_price is not None and provider_price > 0:
        return round(provider_price * markup, 2)
    return None


def _format_service(s: dict, markup: float) -> dict:
    """Normalize a raw service dict into the API response shape."""
    platform_price = _apply_markup(s.get("price"), markup)
    return {
        "id": s["id"],
        "name": s["name"],
        "price": platform_price,
        "cost": platform_price,
        "provider_cost": s.get("price"),
    }


@router.get("/{country}/services")
async def get_services(country: str):
    """Get services with real provider pricing.

    If the provider API fails, return an error — never invent prices.
    """
    settings = get_settings()

    try:
        raw = await _tv.get_services_list()

        if not raw:
            logger.error(f"TextVerified API returned empty services list for {country}")
            return {
                "services": [],
                "total": 0,
                "source": "error",
                "error": "TextVerified API returned no services. Please contact support.",
            }

        logger.info(f"Successfully fetched {len(raw)} services from TextVerified API")

        return {
            "services": [_format_service(s, settings.price_markup) for s in raw],
            "total": len(raw),
            "source": "api",
        }

    except RuntimeError as e:
        logger.error(f"TextVerified API error for {country}: {str(e)}")

        # Dev-mode only: return named services with null prices so UI is navigable
        if settings.environment == "development":
            logger.warning("DEV MODE: Returning service names without prices")
            dev_services = [
                {"id": "telegram", "name": "Telegram"},
                {"id": "whatsapp", "name": "WhatsApp"},
                {"id": "instagram", "name": "Instagram"},
                {"id": "facebook", "name": "Facebook"},
                {"id": "twitter", "name": "Twitter / X"},
                {"id": "google", "name": "Google / Gmail"},
                {"id": "tiktok", "name": "TikTok"},
                {"id": "discord", "name": "Discord"},
                {"id": "snapchat", "name": "Snapchat"},
                {"id": "uber", "name": "Uber"},
                {"id": "amazon", "name": "Amazon"},
                {"id": "paypal", "name": "PayPal"},
                {"id": "linkedin", "name": "LinkedIn"},
                {"id": "microsoft", "name": "Microsoft"},
                {"id": "apple", "name": "Apple"},
            ]
            return {
                "services": [
                    {"id": s["id"], "name": s["name"], "price": None, "cost": None, "provider_cost": None}
                    for s in dev_services
                ],
                "total": len(dev_services),
                "source": "dev-fallback",
                "dev_mode": True,
            }

        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": str(e),
        }
    except Exception as e:
        logger.error(
            f"Unexpected error fetching services for {country}: {str(e)}", exc_info=True
        )
        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": "Failed to fetch services from provider. Please try again.",
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
                "services": [_format_service(s, settings.price_markup) for s in cached],
                "total": len(cached),
                "source": "cache",
            }

        # Cache cold — fetch from API
        raw = await _tv.get_services_list()

        if not raw:
            logger.error(f"TextVerified API returned empty services list for {country}")
            return {
                "services": [],
                "total": 0,
                "source": "error",
                "error": "TextVerified API returned no services",
            }

        return {
            "services": [_format_service(s, settings.price_markup) for s in raw],
            "total": len(raw),
            "source": "warming",
        }

    except RuntimeError as e:
        logger.error(f"TextVerified API error for {country}: {str(e)}")

        if settings.environment == "development":
            logger.warning("DEV MODE: Returning service names without prices")
            dev_services = [
                {"id": "telegram", "name": "Telegram"},
                {"id": "whatsapp", "name": "WhatsApp"},
                {"id": "instagram", "name": "Instagram"},
                {"id": "facebook", "name": "Facebook"},
                {"id": "twitter", "name": "Twitter / X"},
                {"id": "google", "name": "Google / Gmail"},
                {"id": "tiktok", "name": "TikTok"},
                {"id": "discord", "name": "Discord"},
                {"id": "snapchat", "name": "Snapchat"},
                {"id": "uber", "name": "Uber"},
                {"id": "amazon", "name": "Amazon"},
                {"id": "paypal", "name": "PayPal"},
                {"id": "linkedin", "name": "LinkedIn"},
                {"id": "microsoft", "name": "Microsoft"},
                {"id": "apple", "name": "Apple"},
            ]
            return {
                "services": [
                    {"id": s["id"], "name": s["name"], "price": None, "cost": None, "provider_cost": None}
                    for s in dev_services
                ],
                "total": len(dev_services),
                "source": "dev-fallback",
                "dev_mode": True,
            }

        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": str(e),
        }
    except Exception as e:
        logger.error(
            f"Failed to get batch pricing for {country}: {str(e)}", exc_info=True
        )
        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": "Failed to fetch services from provider",
        }
