"""Email verification enforcement."""


from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db

def require_verified_email(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):

    """Dependency to require verified email."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        raise HTTPException(status_code=404, detail="User not found")

if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Check your inbox for verification link.",
        )

    return user_id


def is_email_verified(db: Session, user_id: str) -> bool:

    """Check if user's email is verified."""
    user = db.query(User).filter(User.id == user_id).first()
    return user and user.email_verified
