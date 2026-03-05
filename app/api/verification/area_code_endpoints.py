"""Area Code Endpoints for Verification."""

from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user_id
from app.services.textverified_service import TextVerifiedService
from app.core.unified_cache import cache

router = APIRouter(prefix="/area-codes", tags=["Area Codes"])
_tv = TextVerifiedService()
_CACHE_KEY = "area_codes:US"
_CACHE_TTL = 3600  # 1 hour


@router.get("")
async def get_area_codes(
    country: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    cached = await cache.get(_CACHE_KEY)
    if cached:
        return cached
    codes = await _tv.get_area_codes_list()
    result = {"success": True, "area_codes": codes}
    if codes:
        await cache.set(_CACHE_KEY, result, _CACHE_TTL)
    return result
