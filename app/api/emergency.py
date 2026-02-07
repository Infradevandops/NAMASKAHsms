"""Emergency admin reset endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import bcrypt

router = APIRouter()

RESET_SECRET = "namaskah-emergency-reset-2026"

@router.get("/emergency-create-admin")
async def emergency_create_admin(secret: str, db: Session = Depends(get_db)):
    """Emergency admin creation using ORM - bypasses SQL issues."""
    
    if secret != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    from app.models.user import User
    from app.utils.security import get_password_hash
    import os
    
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Namaskah@Admin2024")
    
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        
        if existing:
            # Update existing user
            existing.password_hash = get_password_hash(ADMIN_PASSWORD)
            existing.is_admin = True
            existing.is_active = True
            existing.email_verified = True
            existing.subscription_tier = "custom"
            existing.credits = max(existing.credits or 0, 10000.0)
            db.commit()
            return {
                "status": "updated",
                "email": ADMIN_EMAIL,
                "id": existing.id,
                "message": "Admin user updated successfully"
            }
        else:
            # Create new admin user using ORM
            admin = User(
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                is_admin=True,
                is_moderator=False,
                is_active=True,
                is_affiliate=False,
                email_verified=True,
                subscription_tier="custom",
                credits=10000.0,
                free_verifications=1000.0,
                bonus_sms_balance=0.0,
                monthly_quota_used=0.0,
                referral_earnings=0.0,
                provider="email",
                failed_login_attempts=0,
                language="en",
                currency="USD"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            return {
                "status": "created",
                "email": ADMIN_EMAIL,
                "id": admin.id,
                "message": "Admin user created successfully"
            }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "type": type(e).__name__}
