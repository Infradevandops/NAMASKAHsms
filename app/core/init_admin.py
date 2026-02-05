"""Initialize admin user on startup if not exists."""

import bcrypt
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

def init_admin_user():
    """Create admin user if it doesn't exist."""
    
    ADMIN_EMAIL = "admin@namaskah.app"
    ADMIN_PASSWORD = "Admin123"
    
    try:
        db = SessionLocal()
        
        # Check if admin exists
        result = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": ADMIN_EMAIL}
        )
        
        if result.fetchone():
            logger.info("Admin user already exists")
            db.close()
            return
        
        # Create admin user
        password_hash = bcrypt.hashpw(
            ADMIN_PASSWORD.encode('utf-8'), 
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
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
        db.close()
        
        logger.info(f"✅ Admin user created: {ADMIN_EMAIL}")
        logger.info(f"✅ Password: {ADMIN_PASSWORD}")
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
