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
router = APIRouter(prefix="/countries", tags=["Services"])
_tv = TextVerifiedService()


@router.get("/{country}/services")
async def get_services(country: str):
    """Get services - MUST return live data from TextVerified API.
    
    NO FALLBACKS. If API fails, return error.
    """
    settings = get_settings()

    try:
        # Get from TextVerified API - this will raise exception if API is down
        raw = await _tv.get_services_list()

        if not raw or len(raw) == 0:
            logger.error(f"TextVerified API returned empty services list for {country}")
            return {
                "services": [],
                "total": 0,
                "source": "error",
                "error": "TextVerified API returned no services. Please contact support.",
            }

        logger.info(f"Successfully fetched {len(raw)} services from TextVerified API")
        
        return {
            "services": [
                {
                    "id": s["id"],          # exact provider ID — must be passed back unchanged
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in raw
            ],
            "total": len(raw),
            "source": "api",
        }

    except RuntimeError as e:
        # TextVerified API is not configured or failed
        logger.error(f"TextVerified API error for {country}: {str(e)}")
        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching services for {country}: {str(e)}", exc_info=True)
        return {
            "services": [],
            "total": 0,
            "source": "error",
            "error": "Failed to fetch services from provider. Please try again.",
        }


@router.get("/{country}/services/batch-pricing")
async def get_services_batch_pricing(country: str):
    """Return services with accurate pricing from 24h cache. Warms cache if cold.
    
    NO FALLBACKS. If API fails, return error.
    """
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

        if not raw or len(raw) == 0:
            logger.error(f"TextVerified API returned empty services list for {country}")
            return {
                "services": [],
                "total": 0,
                "source": "error",
                "error": "TextVerified API returned no services",
            }

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

    except RuntimeError as e:
        logger.error(f"TextVerified API error for {country}: {str(e)}")
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
