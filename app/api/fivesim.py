"""5SIM API endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.fivesim_service import FiveSimService

router = APIRouter(prefix="/5sim", tags=["5SIM"])


@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    """Get 5SIM account balance."""
    try:
        service = FiveSimService()
        return await service.get_balance()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"5SIM service error: {str(e)}")


@router.get("/pricing")
async def get_pricing(
    country: str = "us",
    service: str = "any",
    current_user: User = Depends(get_current_user),
):
    """Get 5SIM pricing for country and service."""
    try:
        fivesim_service = FiveSimService()
        return await fivesim_service.get_pricing(country, service)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"5SIM service error: {str(e)}")


@router.get("/countries")
async def get_countries(current_user: User = Depends(get_current_user)):
    """Get available countries from 5SIM."""
    try:
        service = FiveSimService()
        return await service.get_countries()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"5SIM service error: {str(e)}")


@router.get("/services")
async def get_services(
    country: str = "us", current_user: User = Depends(get_current_user)
):
    """Get available services for country."""
    try:
        service = FiveSimService()
        pricing = await service.get_pricing(country)
        return {"services": list(pricing.keys()) if pricing else []}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"5SIM service error: {str(e)}")
