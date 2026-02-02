

from typing import Any, Dict
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import NotificationSettings, User
from app.models.user_preference import UserPreference
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/user", tags=["User Settings"])


class ChangePasswordRequest(BaseModel):

    old_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):

    password: str


    @router.post("/settings/notifications")
    async def save_notifications(
        data: Dict[str, Any] = Body(...),
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """
        Save notification settings.
        Expects: verification_alerts (bool), payment_receipts (bool)
        """
    # Check if settings exist
        settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()

        if not settings:
        settings = NotificationSettings(
            user_id=user_id,
            email_on_sms=data.get("verification_alerts", True),
            email_on_low_balance=data.get("payment_receipts", True),  # Mapping receipts to this for now
        )
        db.add(settings)
        else:
        settings.email_on_sms = data.get("verification_alerts", settings.email_on_sms)
        settings.email_on_low_balance = data.get("payment_receipts", settings.email_on_low_balance)

        db.commit()
        return {"status": "success", "message": "Notification preferences saved"}


        @router.post("/settings/privacy")
    async def save_privacy(
        data: Dict[str, Any] = Body(...),
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """
        Save privacy settings to UserPreference.
        """
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

        if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)

        pref.profile_visibility = data.get(
        "profile_visibility",
        pref.profile_visibility if pref.profile_visibility is not None else False,
        )
        pref.analytics_tracking = data.get(
        "analytics_tracking",
        pref.analytics_tracking if pref.analytics_tracking is not None else True,
        )
        pref.data_retention = str(
        data.get(
            "data_retention",
            pref.data_retention if pref.data_retention is not None else "90",
        )
        )

        db.commit()
        return {"status": "success", "message": "Privacy settings saved"}


        @router.post("/settings/billing")
    async def save_billing(
        data: Dict[str, Any] = Body(...),
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """
        Save billing settings to UserPreference.
        """
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

        if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)

        pref.billing_email = data.get("billing_email", pref.billing_email)
        pref.billing_address = data.get("billing_address", pref.billing_address)
        pref.auto_recharge = data.get("auto_recharge", pref.auto_recharge if pref.auto_recharge is not None else False)

        recharge_amount = data.get("recharge_amount")
        if recharge_amount:
        try:
            pref.recharge_amount = float(recharge_amount)
        except ValueError:
            pass

        db.commit()
        return {"status": "success", "message": "Billing settings saved"}


        @router.post("/logout-all")
    async def logout_all(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
        """
        Logout all devices by clearing refresh token.
        In a more advanced setup, implementing token versions would be better.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
        user.refresh_token = None
        db.commit()

        return {"status": "success", "message": "Logged out from all devices"}


        @router.post("/delete-account")
    async def delete_account(
        request: DeleteAccountRequest,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """
        Delete user account after verifying password.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid password")

    # In a real app, we might soft delete or archive data.
    # For now, we will perform a hard delete of the user record.
    # Cascading deletes should handle related records if configured,
    # otherwise this might fail if foreign keys exist.
        try:
        db.delete(user)
        db.commit()
        except Exception:
        db.rollback()
        # Fallback to soft delete or just erroring out for safefy
        raise HTTPException(
            status_code=500,
            detail="Could not delete account due to existing dependencies.",
        )

        return {"status": "success", "message": "Account deleted"}


        @router.post("/change-password")
    async def change_password(
        request: ChangePasswordRequest,
        user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        ):
        """Change user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
        raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid old password")

        user.password_hash = hash_password(request.new_password)
        db.commit()

        return {"status": "success", "message": "Password updated successfully"}