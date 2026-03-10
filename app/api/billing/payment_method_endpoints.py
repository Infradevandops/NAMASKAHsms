"""Payment method (card on file) endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user_preference import UserPreference

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
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    has_card = bool(pref and pref.paystack_authorization_code)
    return {
        "has_card": has_card,
        "card_last4": pref.card_last4 if pref else None,
        "card_type": pref.card_type if pref else None,
        "card_expiry": pref.card_expiry if pref else None,
        "auto_recharge_enabled": pref.auto_recharge if pref else False,
    }


@router.post("")
async def save_payment_method(
    data: SaveCardRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
    pref.paystack_authorization_code = data.authorization_code
    pref.card_last4 = data.card_last4
    pref.card_type = data.card_type
    pref.card_expiry = data.card_expiry
    db.commit()
    return {"success": True, "card_last4": data.card_last4, "card_type": data.card_type}


@router.delete("")
async def remove_payment_method(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if pref:
        pref.paystack_authorization_code = None
        pref.card_last4 = None
        pref.card_type = None
        pref.card_expiry = None
        pref.auto_recharge = False
        db.commit()
    return {"success": True}
