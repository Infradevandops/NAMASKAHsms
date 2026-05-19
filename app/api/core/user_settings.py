import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import NotificationSettings, User
from app.models.user_preference import UserPreference
from app.utils.security import get_password_hash as hash_password
from app.utils.security import verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User Settings"])
auth_router = APIRouter(prefix="/api/auth", tags=["Auth"])


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
    """Save notification settings."""
    try:
        settings = (
            db.query(NotificationSettings)
            .filter(NotificationSettings.user_id == user_id)
            .first()
        )

        if not settings:
            settings = NotificationSettings(
                user_id=user_id,
                email_on_sms=data.get("verification_alerts", True),
                email_on_low_balance=data.get("payment_receipts", True),
            )
            db.add(settings)
        else:
            settings.email_on_sms = data.get(
                "verification_alerts", settings.email_on_sms
            )
            settings.email_on_low_balance = data.get(
                "payment_receipts", settings.email_on_low_balance
            )

        db.commit()
        return {"status": "success", "message": "Notification preferences saved"}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error saving notification settings for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to save notification settings"
        )


@router.post("/settings/privacy")
async def save_privacy(
    data: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save privacy settings to UserPreference."""
    try:
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )

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
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error saving privacy settings for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to save privacy settings")


@router.post("/settings/billing")
async def save_billing(
    data: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save billing settings to UserPreference."""
    try:
        pref = (
            db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        )

        if not pref:
            pref = UserPreference(user_id=user_id)
            db.add(pref)

        pref.billing_email = data.get("billing_email", pref.billing_email)
        pref.billing_address = data.get("billing_address", pref.billing_address)
        pref.auto_recharge = data.get(
            "auto_recharge",
            pref.auto_recharge if pref.auto_recharge is not None else False,
        )

        recharge_amount = data.get("recharge_amount")
        if recharge_amount:
            try:
                pref.recharge_amount = float(recharge_amount)
            except ValueError:
                pass

        db.commit()
        return {"status": "success", "message": "Billing settings saved"}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error saving billing settings for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to save billing settings")


@router.post("/logout-all")
async def logout_all(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Logout all devices by clearing refresh token."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.refresh_token = None
        db.commit()

        return {"status": "success", "message": "Logged out from all devices"}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error logging out all devices for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to logout from all devices")


@router.post("/delete-account")
async def delete_account(
    request: DeleteAccountRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete user account after verifying password."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid password")

        try:
            db.delete(user)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Could not delete account due to existing dependencies.",
            )

        return {"status": "success", "message": "Account deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Change user password."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(request.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid old password")

        user.password_hash = hash_password(request.new_password)
        db.commit()

        return {"status": "success", "message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to change password")


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@auth_router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    """Send password reset email."""
    try:
        from datetime import datetime, timedelta, timezone

        user = db.query(User).filter(User.email == request.email).first()
        if user:
            import secrets

            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            try:
                db.commit()
                # Send reset email
                try:
                    from app.core.config import get_settings
                    from app.services.email_service import email_service

                    settings = get_settings()
                    base_url = settings.base_url or "https://vrenum.onrender.com"
                    import asyncio

                    asyncio.create_task(
                        email_service.send_password_reset(user.email, token, base_url)
                    )
                except Exception as email_error:
                    logger.warning(f"Failed to send reset email: {email_error}")
            except Exception:
                db.rollback()
        return {
            "status": "success",
            "message": "If that email exists, a reset link has been sent",
        }
    except Exception as e:
        logger.error(f"Error in forgot password: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to process password reset request"
        )


@auth_router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    try:
        from datetime import datetime, timezone

        user = db.query(User).filter(User.reset_token == request.token).first()
        if not user:
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token"
            )

        if user.reset_token_expires:
            expires = user.reset_token_expires
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Reset token has expired")

        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=400, detail="Password must be at least 8 characters"
            )

        user.password_hash = hash_password(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        return {"status": "success", "message": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset password")


@auth_router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email via token link."""
    try:
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid verification token")

        user.email_verified = True
        user.verification_token = None
        db.commit()

        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/login?verified=true", status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error verifying email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify email")
