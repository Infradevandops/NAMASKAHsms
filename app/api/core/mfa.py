"""MFA (TOTP) endpoints for user two-factor authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.mfa_service import MFAService

router = APIRouter(prefix="/api/user/mfa", tags=["MFA"])


class MFAVerifyRequest(BaseModel):
    token: str


@router.post("/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Generate a new MFA secret and return QR code. Does not enable MFA until verified."""
    secret = MFAService.generate_secret()
    current_user.mfa_secret = secret
    db.commit()
    qr_b64 = MFAService.generate_qr_code(current_user.email, secret)
    return {"secret": secret, "qr_code": qr_b64}


@router.post("/verify")
async def verify_and_enable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify TOTP token and enable MFA on the account."""
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="Call /setup first")
    if not MFAService.verify_token(current_user.mfa_secret, payload.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    current_user.mfa_enabled = True
    db.commit()
    return {"mfa_enabled": True}


@router.post("/disable")
async def disable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable MFA after confirming with a valid token."""
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
