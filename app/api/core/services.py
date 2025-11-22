"""
Services API Router - SMS Service Management
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.unified_cache import cache
from app.models.user import User

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/status")
async def get_services_status():
    """Get status of all SMS services (cached 1h)"""
    # Check cache first
    cache_key_str = cache.cache_key("services", "status")
    cached_result = await cache.get(cache_key_str)
    if cached_result:
        return cached_result

    result = {
        "status": "operational",
        "services": {
            "sms_activate": "active",
            "5sim": "active",
            "textverified": "active",
            "getsms": "active"
        }
    }

    # Cache for 1 hour
    await cache.set(cache_key_str, result, ttl=3600)
    return result


@router.get("/providers")
async def get_providers(current_user: User = Depends(get_current_user)):
    """Get available SMS providers (cached 1h)"""
    # Check cache first
    cache_key_str = cache.cache_key("services", "providers")
    cached_result = await cache.get(cache_key_str)
    if cached_result:
        return cached_result

    result = {
        "providers": [
            {"name": "SMS - Activate", "status": "active", "countries": 180},
            {"name": "5SIM", "status": "active", "countries": 150},
            {"name": "TextVerified", "status": "active", "countries": 50},
            {"name": "GetSMS", "status": "active", "countries": 100}
        ]
    }

    # Cache for 1 hour
    await cache.set(cache_key_str, result, ttl=3600)
    return result
