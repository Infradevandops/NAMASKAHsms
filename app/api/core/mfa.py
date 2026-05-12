"""MFA (TOTP) endpoints for user two-factor authentication."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.mfa_service import MFAService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user/mfa", tags=["MFA"])


class MFAVerifyRequest(BaseModel):
    token: str


@router.post("/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Generate a new MFA secret and return QR code. Does not enable MFA until verified."""
    try:
        secret = MFAService.generate_secret()
        current_user.mfa_secret = secret
        db.commit()
        qr_b64 = MFAService.generate_qr_code(current_user.email, secret)
        return {"secret": secret, "qr_code": qr_b64}
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error setting up MFA for user {current_user.id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to setup MFA")


@router.post("/verify")
async def verify_and_enable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify TOTP token and enable MFA on the account."""
    try:
        if not current_user.mfa_secret:
            raise HTTPException(status_code=400, detail="Call /setup first")
        if not MFAService.verify_token(current_user.mfa_secret, payload.token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        current_user.mfa_enabled = True
        db.commit()
        return {"mfa_enabled": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error verifying MFA for user {current_user.id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to verify MFA")


@router.post("/disable")
async def disable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable MFA after confirming with a valid token."""
    try:
        if not current_user.mfa_enabled or not current_user.mfa_secret:
            raise HTTPException(status_code=400, detail="MFA is not enabled")
        if not MFAService.verify_token(current_user.mfa_secret, payload.token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        current_user.mfa_enabled = False
        current_user.mfa_secret = None
        db.commit()
        return {"mfa_enabled": False}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error disabling MFA for user {current_user.id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to disable MFA")
