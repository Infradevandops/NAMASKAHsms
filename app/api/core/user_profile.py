import logging

logger = logging.getLogger(__name__)
"""User profile API endpoints."""

import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User

router = APIRouter(prefix="/user", tags=["user"])

AVATAR_DIR = "static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    try:
        """Get current user profile."""
        user = db.query(User).filter(User.id == user_id).first()

        return {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_moderator": user.is_moderator,
            "credits": float(user.credits),
            "subscription_tier": user.subscription_tier,
            "onboarding_completed": bool(user.onboarding_completed),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        """Upload user avatar image."""
        if avatar.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400, detail="Invalid file type. Use JPEG, PNG, WebP or GIF."
            )

        contents = await avatar.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=400, detail="File too large. Maximum size is 2MB."
            )

        ext = (
            avatar.filename.rsplit(".", 1)[-1].lower()
            if "." in avatar.filename
            else "jpg"
        )
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(contents)

        avatar_url = f"/static/avatars/{filename}"
        user = db.query(User).filter(User.id == user_id).first()
        user.avatar_url = avatar_url
        db.commit()

        return {"avatar_url": avatar_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_avatar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
