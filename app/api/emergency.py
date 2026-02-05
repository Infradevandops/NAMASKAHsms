"""Emergency admin reset endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESET_SECRET = "namaskah-emergency-reset-2026"  # Change this!

@router.post("/emergency-reset-admin")
async def emergency_reset_admin(secret: str, db: Session = Depends(get_db)):
    """Emergency admin password reset - REMOVE AFTER USE."""
    
    if secret != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    ADMIN_EMAIL = "admin@namaskah.app"
    ADMIN_PASSWORD = "Namaskah@Admin2024"
    password_hash = pwd_context.hash(ADMIN_PASSWORD)
    
    # Check if user exists
    result = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": ADMIN_EMAIL}
    )
    user = result.fetchone()
    
    if user:
        # Update password
        db.execute(
            text("UPDATE users SET password_hash = :hash, is_admin = true WHERE email = :email"),
            {"hash": password_hash, "email": ADMIN_EMAIL}
        )
        db.commit()
        return {"status": "updated", "email": ADMIN_EMAIL}
    else:
        # Create user
        db.execute(
            text("""
                INSERT INTO users (email, password_hash, is_admin, credits, email_verified, created_at)
                VALUES (:email, :hash, true, 1000, true, NOW())
            """),
            {"email": ADMIN_EMAIL, "hash": password_hash}
        )
        db.commit()
        return {"status": "created", "email": ADMIN_EMAIL}
