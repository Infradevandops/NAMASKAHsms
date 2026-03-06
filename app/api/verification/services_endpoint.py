"""Services endpoint for verification system."""

from fastapi import APIRouter
from app.services.textverified_service import TextVerifiedService
from app.core.config import get_settings

router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()


@router.get("/{country}/services")
async def get_services(country: str):
    """Get services with markup applied."""
    settings = get_settings()
    raw = await _tv.get_services_list()
    return {
        "services": [
            {"id": s["id"], "name": s["name"], "price": round(s["price"] * settings.price_markup, 2)}
            for s in raw
        ],
        "total": len(raw),
    }
