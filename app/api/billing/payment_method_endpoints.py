import logging

logger = logging.getLogger(__name__)
"""Payment method (card on file) endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user_preference import UserPreference
from app.services.geolocation_service import geolocation_service

router = APIRouter()


class SaveCardRequest(BaseModel):
    authorization_code: str
    card_last4: str
    card_type: str
    card_expiry: str


@router.get("/status")
async def payment_method_status(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )
        has_card = bool(pref and pref.paystack_authorization_code)
        return {
            "has_card": has_card,
            "card_last4": pref.card_last4 if pref else None,
            "card_type": pref.card_type if pref else None,
            "card_expiry": pref.card_expiry if pref else None,
            "auto_recharge_enabled": pref.auto_recharge if pref else False,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in payment_method_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
async def save_payment_method(
    data: SaveCardRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )
        if not pref:
            pref = UserPreference(user_id=user_id)
            db.add(pref)
        pref.paystack_authorization_code = data.authorization_code
        pref.card_last4 = data.card_last4
        pref.card_type = data.card_type
        pref.card_expiry = data.card_expiry
        db.commit()
        return {
            "success": True,
            "card_last4": data.card_last4,
            "card_type": data.card_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_payment_method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("")
async def remove_payment_method(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )
        if pref:
            pref.paystack_authorization_code = None
            pref.card_last4 = None
            pref.card_type = None
            pref.card_expiry = None
            pref.auto_recharge = False
            db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in remove_payment_method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/methods-by-location")
async def get_payment_methods_by_location(
    request: Request, user_id: str = Depends(get_current_user_id)
):
    try:
        user_country = geolocation_service.detect_country(request)

        PAYMENT_METHODS_BY_COUNTRY = {
            "NG": [
                {
                    "id": "paystack",
                    "name": "Paystack (Cards/Bank)",
                    "fee": 1.5,
                    "icon": "💳",
                },
                {
                    "id": "local_bank_transfer",
                    "name": "Local Bank Transfer",
                    "fee": 0.0,
                    "icon": "🏦",
                },
                {
                    "id": "mobile_money",
                    "name": "Mobile Money",
                    "fee": 1.0,
                    "icon": "📱",
                },
            ],
            "IN": [
                {"id": "upi", "name": "UPI", "fee": 0.0, "icon": "🇮🇳"},
                {"id": "razorpay", "name": "Razorpay", "fee": 2.0, "icon": "💳"},
                {
                    "id": "bank_transfer",
                    "name": "Bank Transfer",
                    "fee": 0.0,
                    "icon": "🏦",
                },
            ],
            "US": [
                {"id": "stripe", "name": "Credit/Debit Card", "fee": 2.9, "icon": "💳"},
                {"id": "paypal", "name": "PayPal", "fee": 3.4, "icon": "🅿️"},
            ],
            "GB": [
                {"id": "stripe", "name": "Credit/Debit Card", "fee": 1.4, "icon": "💳"},
                {
                    "id": "bank_transfer",
                    "name": "Bank Transfer",
                    "fee": 0.0,
                    "icon": "🏦",
                },
            ],
            "default": [
                {"id": "stripe", "name": "Credit/Debit Card", "fee": 2.9, "icon": "💳"},
                {
                    "id": "bank_transfer",
                    "name": "Bank Transfer",
                    "fee": 0.0,
                    "icon": "🏦",
                },
            ],
        }

        recommended = PAYMENT_METHODS_BY_COUNTRY.get(
            user_country, PAYMENT_METHODS_BY_COUNTRY["default"]
        )

        # We can also return all methods if the user wants to see other options
        all_methods = [
            {"id": "paystack", "name": "Paystack", "fee": 1.5, "icon": "💳"},
            {"id": "stripe", "name": "Stripe", "fee": 2.9, "icon": "💳"},
            {"id": "paypal", "name": "PayPal", "fee": 3.4, "icon": "🅿️"},
            {
                "id": "local_bank_transfer",
                "name": "Local Bank Transfer",
                "fee": 0.0,
                "icon": "🏦",
            },
            {"id": "mobile_money", "name": "Mobile Money", "fee": 1.0, "icon": "📱"},
            {"id": "upi", "name": "UPI", "fee": 0.0, "icon": "🇮🇳"},
        ]

        return {
            "country": user_country,
            "recommended_methods": recommended,
            "all_methods": all_methods,
        }
    except Exception as e:
        logger.error(f"Error getting methods by location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
