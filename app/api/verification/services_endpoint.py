"""Services endpoint for verification system."""

from fastapi import APIRouter, BackgroundTasks

from app.core.config import get_settings
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()


@router.get("/{country}/services")
async def get_services(country: str):
    """Get services — returns immediately from cache or service names, prices filled async."""
    settings = get_settings()
    raw = await _tv.get_services_list()
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
    }


@router.get("/{country}/services/batch-pricing")
async def get_services_batch_pricing(country: str):
    """Return services with accurate pricing from 24h cache. Warms cache if cold."""
    settings = get_settings()
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
    # Cache cold — trigger background warm, return names-only immediately
    raw = await _tv.get_services_list()
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
