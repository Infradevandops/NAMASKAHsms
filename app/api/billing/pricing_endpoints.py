"""Pricing estimation endpoints - Non-conflicting with tier system."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.get("/estimate")
async def estimate_verification_cost(
    service: str = Query(..., description="Service name (telegram, whatsapp, etc)"),
    country: str = Query("US", description="Country code"),
    quantity: int = Query(1, ge=1, le=1000, description="Number of verifications"),
    db: Session = Depends(get_db),
):
    """Estimate cost for verification(s) using new pricing system."""
    try:
        # Simple estimation - always use Pay-As-You-Go pricing for estimates
        base_cost = 2.50  # Pay-As-You-Go rate
        total_cost = base_cost * quantity

        return {
            "service": service,
            "country": country,
            "quantity": quantity,
            "cost_per_sms": base_cost,
            "total_cost": total_cost,
            "currency": "USD",
            "note": "Actual cost may vary based on your subscription tier",
        }

    except Exception as e:
        logger.error(f"Failed to estimate cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to estimate cost"
        )


@router.get("/services")
async def get_available_services():
    """Get list of available services."""
    services = {
        "telegram": "Telegram",
        "whatsapp": "WhatsApp",
        "google": "Google",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "twitter": "Twitter",
        "discord": "Discord",
        "tiktok": "TikTok",
    }

    return {"services": services, "total": len(services)}


@router.get("/countries")
async def get_available_countries():
    """Get list of available countries."""
    countries = {
        "US": "United States",
        "CA": "Canada",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
    }

    return {"countries": countries, "total": len(countries)}
