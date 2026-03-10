"""Role-Based Access Control (RBAC) system."""

from enum import Enum

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


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

    if hasattr(user, "is_moderator") and user.is_moderator:
        return Role.MODERATOR

    return Role.USER


def require_role(required_role: Role):
    """Dependency factory for role-based access control."""

    def check_role(db: Session = Depends(get_db)):
        def inner(user_id: str):
            role = get_user_role(db, user_id)
            role_hierarchy = {
                Role.GUEST: 0,
                Role.USER: 1,
                Role.MODERATOR: 2,
                Role.ADMIN: 3,
            }

            if role_hierarchy.get(role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role.value} role",
                )
            return user_id

        return inner

    return check_role
