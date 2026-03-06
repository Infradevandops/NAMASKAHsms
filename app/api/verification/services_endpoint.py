"""Services endpoint for verification system."""

from fastapi import APIRouter
from app.services.textverified_service import TextVerifiedService
from app.core.config import get_settings
from app.core.unified_cache import cache

router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()
_CACHE_KEY = "services:US"
_CACHE_TTL = 7200  # 2 hours


@router.get("/{country}/services")
async def get_services(country: str):
    cached = await cache.get(_CACHE_KEY)
    if cached:
        return cached
    settings = get_settings()
    raw = await _tv.get_services_list()
    result = {
        "services": [
            {"id": s["id"], "name": s["name"], "price": round(s["price"] * settings.price_markup, 2)}
            for s in raw
        ],
        "total": len(raw),
    }
    await cache.set(_CACHE_KEY, result, _CACHE_TTL)
    return result
