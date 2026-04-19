"""Pricing Endpoints for Verification."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.pricing_calculator import PricingCalculator
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/pricing", tags=["Pricing"])


async def _get_provider_price(service: str) -> Optional[float]:
    """Look up real provider price from cache/API."""
    try:
        tv = TextVerifiedService()
        services = await tv.get_services_list()
        for s in services:
            if s["id"] == service:
                return s.get("price")
    except Exception:
        pass
    return None


@router.get("")
async def get_pricing(
    service: str = Query(..., description="Service name (e.g., whatsapp)"),
    area_code: str = Query(None, description="Optional area code (e.g., 212)"),
    carrier: str = Query(None, description="Optional carrier (e.g., tmobile)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Calculate pricing with real provider costs, premiums, and discounts."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(tier="freemium")

    provider_price = await _get_provider_price(service)

    filters = {"area_code": area_code, "carrier": carrier}
    pricing = PricingCalculator.calculate_sms_cost(
        db, user_id=user.id, filters=filters, provider_price=provider_price
    )

    return {"success": True, "pricing": pricing}
