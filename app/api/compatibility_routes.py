"""API Compatibility Layer - Route Aliases for Frontend"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()

# Alias: /api/billing/balance -> /api/wallet/balance
@router.get("/billing/balance")
async def billing_balance_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from app.api.billing.credit_endpoints import get_credit_balance
    return await get_credit_balance(user_id, db)

# Alias: /api/user/me -> /api/auth/me
@router.get("/user/me")
async def user_me_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.email.split('@')[0],
        "credits": float(user.credits) if user.credits else 0.0,
        "is_active": user.is_active,
    }

# Alias: /api/tiers/current -> /api/billing/tiers/current
@router.get("/tiers/current")
async def tiers_current_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from app.api.billing.tier_endpoints import get_current_tier
    return await get_current_tier(user_id, db)

# Alias: /api/tiers/ -> /api/billing/tiers/available
@router.get("/tiers/")
async def tiers_list_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from app.api.billing.tier_endpoints import get_available_tiers
    return await get_available_tiers(user_id, db)

# Alias: /api/tiers -> /api/billing/tiers/available
@router.get("/tiers")
async def tiers_alias(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from app.api.billing.tier_endpoints import get_available_tiers
    return await get_available_tiers(user_id, db)

# Stub: /api/notifications/categories
@router.get("/notifications/categories")
async def notification_categories():
    return {
        "categories": [
            {"id": "system", "name": "System", "enabled": True},
            {"id": "payment", "name": "Payment", "enabled": True},
            {"id": "verification", "name": "Verification", "enabled": True},
            {"id": "security", "name": "Security", "enabled": True}
        ]
    }

# Stub: /api/user/settings
@router.get("/user/settings")
async def user_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    return {
        "email": user.email if user else "",
        "notifications_enabled": True,
        "language": "en",
        "timezone": "UTC"
    }
