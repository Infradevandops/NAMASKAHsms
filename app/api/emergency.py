"""Emergency admin reset endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import bcrypt

router = APIRouter()

RESET_SECRET = "namaskah-emergency-reset-2026"

@router.get("/emergency-reset-admin")
async def emergency_reset_admin(secret: str, db: Session = Depends(get_db)):
    """Emergency admin password reset - REMOVE AFTER USE."""
    
    if secret != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    ADMIN_EMAIL = "admin@namaskah.app"
    ADMIN_PASSWORD = "Admin123"  # Simpler password
    
    # Hash password with bcrypt - use rounds=12 like production
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    try:
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
            return {"status": "updated", "email": ADMIN_EMAIL, "hash": password_hash[:20], "password": ADMIN_PASSWORD}
        else:
            # Create user with all required fields
            db.execute(
                text("""
                    INSERT INTO users (
                        email, password_hash, is_admin, is_moderator, credits, 
                        free_verifications, email_verified, subscription_tier, 
                        bonus_sms_balance, monthly_quota_used, referral_earnings, 
                        provider, failed_login_attempts, language, currency, created_at
                    )
                    VALUES (
                        :email, :hash, true, false, 1000, 
                        1.0, true, 'freemium', 
                        0.0, 0.0, 0.0, 
                        'email', 0, 'en', 'USD', NOW()
                    )
                """),
                {"email": ADMIN_EMAIL, "hash": password_hash}
            )
            db.commit()
            return {"status": "created", "email": ADMIN_EMAIL, "hash": password_hash[:20], "password": ADMIN_PASSWORD}
    except Exception as e:
        return {"error": str(e)}
