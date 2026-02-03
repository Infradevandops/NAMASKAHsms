"""Country and area code API endpoints - US only via TextVerified."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/countries", tags=["Countries"])


@router.get("/")
async def get_countries() -> Dict[str, Any]:
    """Get list of supported countries - Currently US only via TextVerified."""
    # TextVerified API only supports US numbers
    countries = [
        {
            "code": "US",
            "name": "United States",
            "flag": "🇺🇸",
            "supported": True,
            "area_codes_available": True,
            "carriers_available": True,
            "default": True,
            "note": "Primary supported country via TextVerified API"
        }
    ]

    return {
        "success": True,
        "countries": countries,
        "total": len(countries),
        "provider": "TextVerified",
        "note": "Currently only US numbers are supported through our TextVerified integration"
    }


@router.get("/usa/area-codes")
async def get_usa_area_codes() -> Dict[str, Any]:
    """Get all US area codes from TextVerified API."""
    try:
        integration = TextVerifiedService()
        raw_codes = await integration.get_area_codes_list()

        # Transform to frontend-expected format
        area_codes = []
        for code_data in raw_codes:
            # Extract code and name (handle different possible fields)
            area_code = code_data.get("code") or code_data.get("area_code")
            name = code_data.get("name") or code_data.get("region") or code_data.get("state")

            # Skip if code or name is missing/null
            if not area_code or not name:
                continue

            area_codes.append({
                "code": str(area_code),
                "name": str(name),
                "country": "US",
                "available": code_data.get("available", True),
            })

        result = {
            "success": True,
            "country": "United States",
            "area_codes": area_codes,
            "total": len(area_codes),
            "provider": "TextVerified"
        }

        return result

    except Exception as e:
        logger.error(f"Failed to get area codes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load area codes")


@router.get("/usa/carriers")
async def get_usa_carriers() -> Dict[str, Any]:
    """Get available US carriers."""
    try:
        carriers = [
            {"id": "verizon", "name": "Verizon"},
            {"id": "att", "name": "AT&T"},
            {"id": "tmobile", "name": "T-Mobile"},
            {"id": "sprint", "name": "Sprint"},
            {"id": "us_cellular", "name": "US Cellular"},
            {"id": "any", "name": "Any Carrier"},
        ]

        return {
            "success": True,
            "country": "United States",
            "carriers": carriers,
            "total": len(carriers),
            "provider": "TextVerified"
        }

    except Exception as e:
        logger.error(f"Failed to get carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load carriers")


@router.get("/us")
@router.get("/usa")
@router.get("/US")
async def get_us_info() -> Dict[str, Any]:
    """Get information about US support."""
    return {
        "success": True,
        "country": {
            "code": "US",
            "name": "United States",
            "flag": "🇺🇸",
            "supported": True,
            "area_codes_available": True,
            "carriers_available": True,
            "provider": "TextVerified",
            "features": [
                "Area code selection",
                "Carrier filtering", 
                "Real-time SMS delivery",
                "Multiple service support"
            ]
        }
    }


@router.get("/{country_code}")
async def get_country_info(country_code: str) -> Dict[str, Any]:
    """Get information about a specific country - Only US is supported."""
    country_code = country_code.upper()
    
    if country_code == "US":
        return {
            "success": True,
            "country": {
                "code": "US",
                "name": "United States",
                "flag": "🇺🇸",
                "supported": True,
                "area_codes_available": True,
                "carriers_available": True,
                "provider": "TextVerified"
            }
        }
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Country '{country_code}' is not supported. Only US numbers are available through TextVerified."
        )