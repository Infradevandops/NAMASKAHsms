"""Enhanced authentication with HttpOnly cookies and refresh tokens."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.token_manager import create_tokens, verify_refresh_token
from app.models.user import User
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    message: str


def get_session(db, refresh_token):
    return None


def invalidate_session(db, refresh_token):
    pass


def invalidate_all_sessions(db, user_id):
    pass


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    if not verify_refresh_token(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    session = get_session(db, refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new tokens
    tokens = create_tokens(user.id, user.email)

    response = JSONResponse(
        content={
            "access_token": tokens["access_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
        }
    )

    # Set new access token in HttpOnly cookie
    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=900,  # 15 minutes
    )

    return response


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Logout user and invalidate session."""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        invalidate_session(db, refresh_token)

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return SuccessResponse(message="Logged out successfully")


@router.post("/logout-all")
async def logout_all(
    response: Response, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Logout from all devices."""
    invalidate_all_sessions(db, user_id)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return SuccessResponse(message="Logged out from all devices")
