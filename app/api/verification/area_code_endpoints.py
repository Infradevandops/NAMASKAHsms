"""Area Code Endpoints for Verification."""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user_id
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService
from app.services.purchase_intelligence import PurchaseIntelligenceService
from app.services.area_code_geo import NANPA_DATA, get_nearby, filter_supported

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

@router.get("/check")
async def check_area_code_availability(
    request: Request,
    area_code: str = Query(...),
    service: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Check the availability of an area code for a specific service based on historical purchase data.
    Does not require auth (reduces friction for type-ahead). Rate limited by IP.
    """
    if not area_code.isdigit() or len(area_code) < 3:
        raise HTTPException(status_code=400, detail="Invalid area code")
        
    area_code = area_code[:3]
    
    if area_code not in NANPA_DATA:
        raise HTTPException(status_code=400, detail="Unknown area code")
        
    # Get TextVerified supported list
    cached_list = await cache.get(_CACHE_KEY)
    if not cached_list:
        codes = await _tv.get_area_codes_list()
        cached_list = {"success": True, "area_codes": codes}
        if codes:
            await cache.set(_CACHE_KEY, cached_list, _CACHE_TTL)
            
    tv_supported = cached_list.get("area_codes", [])
    
    # TextVerified formats differently, extracting array of pure strings
    supported_strings = []
    for item in tv_supported:
        if isinstance(item, dict) and "area_code" in item:
            supported_strings.append(str(item["area_code"]))
        else:
            supported_strings.append(str(item))
            
    if area_code not in supported_strings:
        raise HTTPException(status_code=400, detail="Area code not supported by provider")
        
    try:
        # Score the requested code
        score = await PurchaseIntelligenceService.score_availability(service, area_code)
        
        status = "unknown"
        if score.available is True:
            status = "available"
        elif score.available is False:
            status = "unavailable"
            
        response = {
            "area_code": area_code,
            "service": service,
            "status": status,
            "confidence": score.confidence
        }
        
        if status == "available":
            response["message"] = f"{area_code} is available for {service} based on recent activity."
            
        elif status == "unknown":
            response["message"] = f"No availability data yet for {area_code} + {service}. You can proceed \u2014 if unavailable, you won't be charged."
            # Show unknowns their alternatives as well just in case they decide to switch.
            response["alternatives"] = await _build_alternatives(db, service, area_code, supported_strings)
            
        elif status == "unavailable":
            response["message"] = f"{area_code} is not available for {service}. Select from nearby area codes."
            response["alternatives"] = await _build_alternatives(db, service, area_code, supported_strings)
            
        return response
    except Exception as e:
        # Graceful degradation on db failures
        return {
            "area_code": area_code,
            "service": service,
            "status": "unknown",
            "confidence": 0.0,
            "message": "Availability will be confirmed on purchase. You won't be charged if unavailable.",
            "alternatives": []
        }

async def _build_alternatives(db: Session, service: str, target_code: str, supported_strings: list) -> list:
    nearby = get_nearby(target_code, max_results=15)
    
    # Filter by TV supported
    supported_nearby = [x for x in nearby if x["area_code"] in supported_strings]
    
    alternatives = []
    for alt in supported_nearby:
        alt_score = await PurchaseIntelligenceService.score_availability(service, alt["area_code"])
        
        alt_status = "unknown"
        if alt_score.available is True:
            alt_status = "available"
        elif alt_score.available is False:
            alt_status = "unavailable"
            
        alternatives.append({
            "area_code": alt["area_code"],
            "city": alt["city"],
            "state": alt["state"],
            "proximity": alt["proximity"],
            "status": alt_status,
            "confidence": alt_score.confidence
        })
        
    # Sort alternatives as required:
    # `same_city available` -> `same_city unknown` -> `nearby available` -> `same_state available`
    
    def sort_key(item):
        prox_order = {"same_city": 0, "nearby": 1, "same_state": 2}
        status_order = {"available": 0, "unknown": 1, "unavailable": 2}
        return (
            prox_order.get(item["proximity"], 99),
            status_order.get(item["status"], 99)
        )
        
    alternatives.sort(key=sort_key)
    
    # Cap at 8
    return alternatives[:8]
