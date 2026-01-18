"""Role-Based Access Control (RBAC) system."""

from enum import Enum
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db


class Role(str, Enum):
    """User roles."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


def get_user_role(db: Session, user_id: str) -> Role:
    """Get user's role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return Role.GUEST

    if user.is_admin:
        return Role.ADMIN

    # Check for moderator role (can be added to User model later)
    if hasattr(user, "is_moderator") and user.is_moderator:
        return Role.MODERATOR

    return Role.USER


def require_role(*allowed_roles: Role):
    """Dependency to require specific roles."""

    async def check_role(
        user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
    ):
        user_role = get_user_role(db, user_id)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {', '.join(allowed_roles)}",
            )
        return user_id

    return check_role


def require_admin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Dependency to require admin role."""
    user_role = get_user_role(db, user_id)
    if user_role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


def require_moderator_or_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Dependency to require moderator or admin role."""
    user_role = get_user_role(db, user_id)
    if user_role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Moderator or admin access required"
        )
    return user_id
