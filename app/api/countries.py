"""Countries API for 5SIM integration."""
from fastapi import APIRouter, HTTPException
from app.services.fivesim_service import FiveSimService

router = APIRouter(prefix="/countries", tags=["Countries"])

@router.get("/")
async def get_countries():
    """Get available countries from 5SIM."""
    try:
        service = FiveSimService()
        return await service.get_countries()
    except Exception as e:
        raise HTTPException(status_code=503, detail="Countries service unavailable")

@router.get("/{country}/pricing")
async def get_country_pricing(country: str, service: str = "any"):
    """Get pricing for specific country and service."""
    try:
        fivesim = FiveSimService()
        return await fivesim.get_pricing(country, service)
    except Exception as e:
        raise HTTPException(status_code=503, detail="Pricing service unavailable")