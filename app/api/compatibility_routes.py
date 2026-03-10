"""API Compatibility Layer - Route Aliases for Frontend"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter()


class UserSettingsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    sms_alerts: Optional[bool] = None
    analytics_consent: Optional[bool] = None
    marketing_consent: Optional[bool] = None


# Alias: /api/billing/balance -> /api/wallet/balance
@router.get("/billing/balance")
async def billing_balance_alias(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    from app.api.billing.credit_endpoints import get_credit_balance

    return await get_credit_balance(user_id, db)


# Alias: /api/user/me -> /api/auth/me
@router.get("/user/me")
async def user_me_alias(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.email.split("@")[0],
        "credits": float(user.credits) if user.credits else 0.0,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "tier": getattr(user, "subscription_tier", "freemium"),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# Alias: /api/tiers/current -> /api/billing/tiers/current
@router.get("/tiers/current")
async def tiers_current_alias(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    from app.api.billing.tier_endpoints import get_current_tier

    return await get_current_tier(user_id, db)


# Alias: /api/tiers/ -> /api/billing/tiers/available
@router.get("/tiers/")
async def tiers_list_alias(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    from app.api.billing.tier_endpoints import get_available_tiers

    return await get_available_tiers(user_id, db)


# Alias: /api/tiers -> /api/billing/tiers/available
@router.get("/tiers")
async def tiers_alias(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
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
            {"id": "security", "name": "Security", "enabled": True},
        ]
    }


# Stub: /api/user/settings
@router.get("/user/settings")
async def user_settings(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.email.split("@")[0],
        "email_notifications": getattr(user, "email_notifications", True),
        "sms_alerts": getattr(user, "sms_alerts", False),
        "analytics_consent": getattr(user, "analytics_consent", False),
        "marketing_consent": getattr(user, "marketing_consent", False),
        "language": "en",
        "timezone": "UTC",
        "created_at": (
            user.created_at.isoformat() if hasattr(user, "created_at") else None
        ),
    }


@router.put("/user/settings")
async def update_user_settings(
    payload: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.dict(exclude_none=True).items():
        if hasattr(user, field):
            setattr(user, field, value)
    db.commit()
    return {"message": "Settings updated"}


@router.get("/user/activity")
async def user_activity(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import desc

        from app.models.audit_log import AuditLog

        logs = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(50)
            .all()
        )
        return {
            "activities": [
                {
                    "event": l.event,
                    "details": getattr(l, "details", ""),
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in logs
            ]
        }
    except Exception:
        return {"activities": []}


@router.get("/billing/payment-status/{reference}")
async def billing_payment_status(
    reference: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        from app.models.transaction import Transaction

        tx = (
            db.query(Transaction)
            .filter(Transaction.reference == reference, Transaction.user_id == user_id)
            .first()
        )
        if tx:
            return {
                "status": tx.status,
                "reference": reference,
                "amount": float(tx.amount or 0),
            }
        return {"status": "pending", "reference": reference}
    except Exception:
        return {"status": "pending", "reference": reference}


@router.get("/billing/crypto-addresses")
async def billing_crypto_addresses(user_id: str = Depends(get_current_user_id)):
    settings = get_settings()
    return {
        "btc_address": getattr(settings, "btc_address", ""),
        "eth_address": getattr(settings, "eth_address", ""),
        "sol_address": getattr(settings, "sol_address", ""),
        "ltc_address": getattr(settings, "ltc_address", ""),
    }
