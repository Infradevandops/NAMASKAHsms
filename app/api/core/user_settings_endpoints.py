"""User settings management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.user import NotificationSettings, Referral, User, Webhook
from app.models.user_preference import UserPreference
from app.models.verification import Verification
from app.models.transaction import Transaction

logger = get_logger(__name__)
router = APIRouter(prefix="/api/user", tags=["User Settings"])


class UserSettingsUpdate(BaseModel):
    email_notifications: bool = True
    sms_alerts: bool = False


@router.get("/settings")
async def get_user_settings(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        prefs = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()
        if not prefs:
            prefs = NotificationSettings(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return {"email_notifications": prefs.email_on_sms, "sms_alerts": prefs.email_on_low_balance}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")


@router.put("/settings")
async def update_user_settings(settings: UserSettingsUpdate, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        prefs = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()
        if not prefs:
            prefs = NotificationSettings(user_id=user_id)
            db.add(prefs)
        prefs.email_on_sms = settings.email_notifications
        prefs.email_on_low_balance = settings.sms_alerts
        db.commit()
        logger.info(f"Settings updated for user {user_id}")
        return {"success": True, "message": "Settings updated successfully", "settings": {"email_notifications": prefs.email_on_sms, "sms_alerts": prefs.email_on_low_balance}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")


@router.get("/privacy")
async def get_privacy(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    return {
        "analytics": pref.analytics_tracking if pref else True,
        "marketing": False,
        "email": True,
        "last_export": None,
    }


@router.post("/privacy")
async def save_privacy(data: dict, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
    pref.analytics_tracking = data.get("analytics", pref.analytics_tracking if pref.analytics_tracking is not None else True)
    db.commit()
    return {"status": "success"}


@router.post("/export")
async def export_data(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    verifications = db.query(Verification).filter(Verification.user_id == user_id).all()
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    payload = {
        "profile": {"id": user.id, "email": user.email, "created_at": str(user.created_at)},
        "verifications": [{"id": v.id, "phone_number": v.phone_number, "status": v.status, "created_at": str(v.created_at)} for v in verifications],
        "transactions": [{"id": t.id, "amount": t.amount, "type": t.transaction_type, "created_at": str(t.created_at)} for t in transactions],
    }
    return JSONResponse(content=payload, headers={"Content-Disposition": "attachment; filename=namaskah-data.json"})


@router.get("/referrals")
async def get_referrals(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    referrals = db.query(Referral).filter(Referral.referrer_id == user_id).all()
    return {
        "referral_code": user.referral_code,
        "total_earnings": user.referral_earnings or 0.0,
        "total_referrals": len(referrals),
        "bonus_credits": 0,
        "referrals": [{"user_id": r.referred_id, "created_at": str(r.created_at)} for r in referrals],
    }


@router.get("/webhooks")
async def get_webhooks(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    hooks = db.query(Webhook).filter(Webhook.user_id == user_id, Webhook.is_active == True).all()
    return {"webhooks": [{"id": h.id, "name": h.name, "url": h.url, "events": h.events.split(",") if h.events != "*" else ["*"]} for h in hooks]}
