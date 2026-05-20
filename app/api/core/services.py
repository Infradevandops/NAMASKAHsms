"""
Services API Router - SMS Service Management
"""

import logging

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.unified_cache import cache
from app.models.user import User

logger = logging.getLogger(__name__)
from fastapi import HTTPException

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/status")
async def get_services_status():
    try:
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
                "getsms": "active",
            },
        }

        # Cache for 1 hour
        await cache.set(cache_key_str, result, ttl=3600)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_services_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/providers")
async def get_providers(current_user: User = Depends(get_current_user)):
    try:
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
                {"name": "GetSMS", "status": "active", "countries": 100},
            ]
        }

        # Cache for 1 hour
        await cache.set(cache_key_str, result, ttl=3600)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
