"""Pricing Endpoints for Verification."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.get("")
async def get_pricing(
    service: str = Query(..., description="Service name (e.g., whatsapp)"),
    area_code: str = Query(None, description="Optional area code (e.g., 212)"),
    carrier: str = Query(None, description="Optional carrier (e.g., tmobile)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Calculate pricing with all premiums and discounts.

    Returns detailed pricing breakdown including:
    - Base price for service
    - Area code premium (if applicable)
    - Carrier premium (if applicable)
    - Tier discount (if applicable)
    - Total price
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        # Return default pricing for anonymous users
        user = User(tier="freemium")

    # Calculate pricing
    pricing_service = PricingService()
    pricing = pricing_service.calculate_price(service, user, area_code, carrier)

    return {"success": True, "pricing": pricing}
