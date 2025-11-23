"""FastAPI dependency injection utilities."""
import jwt
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db

security = HTTPBearer(auto_error=False)


def get_token_from_request(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header or cookies."""
    if credentials:
        return credentials.credentials

    token = request.cookies.get("access_token")
    if token:
        return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(
    token: str = Depends(get_token_from_request),
) -> str:
    """Get current user ID from JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current user object from database."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_admin_user_id(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
) -> str:
    """Get admin user ID (requires admin role)."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user_id


def get_current_admin_user(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current admin user object (requires admin role)."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user
