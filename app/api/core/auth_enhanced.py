"""Enhanced authentication with HttpOnly cookies and refresh tokens."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.token_manager import create_tokens, verify_refresh_token
from app.models.user import User


class SuccessResponse(BaseModel):
    message: str


def get_session(db, refresh_token):
    return None


def invalidate_session(db, refresh_token):
    pass


def invalidate_all_sessions(db, user_id):
    pass


router = APIRouter(prefix="/auth", tags=["Authentication"])


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

    tokens = create_tokens(user.id, user.email)

    response = JSONResponse(
        content={
            "access_token": tokens["access_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
        }
    )

    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=900,
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
    from app.services.auth_service import AuthService

    # Revoke the current access token via JTI blacklist
    token = None
    if request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"].split(" ", 1)[1]
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]

    if token:
        AuthService(db).revoke_token(token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return SuccessResponse(message="Logged out successfully")


@router.post("/logout-all")
async def logout_all(
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Logout from all devices — revokes current token and sets a user-level block."""
    from app.core.cache import cache
    from app.services.auth_service import AuthService

    # Revoke current token
    token = None
    if request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"].split(" ", 1)[1]
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]
    if token:
        AuthService(db).revoke_token(token)

    # Set a user-level block key — all tokens issued before now are invalid
    try:
        redis = cache.get_client()
        if redis:
            redis.setex(f"logout_all:{user_id}", 86400 * 30, "1")
    except Exception:
        pass

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return SuccessResponse(message="Logged out from all devices")
