"""Setup and initialization endpoints."""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.auth_security import hash_password
from app.core.database import get_db
from app.models.user import User
from app.schemas.response import SuccessResponse
import os

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("/init - admin", response_model=SuccessResponse)
def initialize_admin(db: Session = Depends(get_db)):

    """Initialize admin user - public endpoint for first - time setup."""

    admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")
    admin_password = os.getenv("ADMIN_PASSWORD")

if not admin_password:
        return SuccessResponse(
            message="Admin setup requires ADMIN_PASSWORD environment variable",
            data={"error": "Missing ADMIN_PASSWORD"},
        )

try:
        # Check if any admin exists
        existing_admin = db.query(User).filter(User.is_admin).first()
if existing_admin:
            return SuccessResponse(
                message="Admin already exists",
                data={"email": admin_email, "note": "Use existing admin credentials"},
            )

        # Check if user exists
        existing_user = db.query(User).filter(User.email == admin_email).first()
if existing_user:
            # Upgrade to admin
            existing_user.is_admin = True
            existing_user.credits = 1000.0
            existing_user.email_verified = True
            db.commit()
            return SuccessResponse(message="User upgraded to admin", data={"email": admin_email})

        # Create new admin
        admin_user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            credits=1000.0,
            is_admin=True,
            email_verified=True,
        )

        db.add(admin_user)
        db.commit()

        return SuccessResponse(
            message="Admin created successfully",
            data={"email": admin_email, "credits": 1000},
        )

except Exception as e:
        return SuccessResponse(
            message=f"Setup failed: {str(e)}",
            data={"email": admin_email, "note": "Try logging in anyway"},
        )