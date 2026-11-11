"""Subscription add-on endpoints — PAYG API access add-on ($10/month)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.subscription_addon import SubscriptionAddon
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/billing/addons", tags=["Billing"])

ADDON_PRICE_USD = 10.0


@router.post("/api-access/subscribe")
async def subscribe_api_addon(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Initialize Paystack payment for PAYG API access add-on ($10/month)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if (user.subscription_tier or "freemium") not in ("payg",):
        raise HTTPException(
            status_code=400,
            detail="API add-on is only available for PAYG users. Pro/Custom already includes API access.",
        )

    existing = (
        db.query(SubscriptionAddon)
        .filter(
            SubscriptionAddon.user_id == user_id,
            SubscriptionAddon.addon_type == "api_access",
            SubscriptionAddon.active.is_(True),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="API access add-on already active.")

    from app.services.payment_service import PaymentService

    payment_service = PaymentService(db)
    result = await payment_service.initialize_payment(
        user_id=user_id,
        email=user.email,
        amount_usd=ADDON_PRICE_USD,
        metadata={"addon_type": "api_access", "user_id": user_id},
    )
    return result


@router.delete("/api-access/cancel", status_code=200)
async def cancel_api_addon(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel PAYG API access add-on. Revokes all API keys immediately."""
    addon = (
        db.query(SubscriptionAddon)
        .filter(
            SubscriptionAddon.user_id == user_id,
            SubscriptionAddon.addon_type == "api_access",
            SubscriptionAddon.active.is_(True),
        )
        .first()
    )
    if not addon:
        raise HTTPException(status_code=404, detail="No active API add-on found.")

    addon.active = False
    addon.expires_at = datetime.now(timezone.utc)

    # Revoke all API keys
    from app.models.api_key import APIKey
    db.query(APIKey).filter(
        APIKey.user_id == user_id, APIKey.is_active.is_(True)
    ).update({"is_active": False})

    db.commit()
    logger.info(f"API add-on cancelled for user {user_id}, keys revoked")
    return {"success": True, "message": "API add-on cancelled and keys revoked."}


@router.get("/status")
async def get_addon_status(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get active add-ons for current user."""
    addons = (
        db.query(SubscriptionAddon)
        .filter(SubscriptionAddon.user_id == user_id, SubscriptionAddon.active.is_(True))
        .all()
    )
    return {
        "addons": [
            {
                "type": a.addon_type,
                "price_usd": float(a.price_usd),
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in addons
        ]
    }
