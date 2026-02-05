"""Initialize admin user on startup if not exists."""

import bcrypt
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

def init_admin_user():
    """Create or update admin user."""
    
    ADMIN_EMAIL = "admin@namaskah.app"
    ADMIN_PASSWORD = "Namaskah@Admin2024"
    
    try:
        db = SessionLocal()
        
        # Check if admin exists
        result = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": ADMIN_EMAIL}
        )
        user = result.fetchone()
        
        # Hash password
        password_hash = bcrypt.hashpw(
            ADMIN_PASSWORD.encode('utf-8'), 
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        if user:
            # Update existing user
            db.execute(
                text("UPDATE users SET password_hash = :hash, is_admin = true WHERE email = :email"),
                {"hash": password_hash, "email": ADMIN_EMAIL}
            )
            db.commit()
            logger.info(f"✅ Admin user updated: {ADMIN_EMAIL}")
        else:
            # Create new admin user
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
            logger.info(f"✅ Admin user created: {ADMIN_EMAIL}")
        
        db.close()
        logger.info(f"✅ Password: {ADMIN_PASSWORD}")
        
    except Exception as e:
        logger.error(f"Failed to init admin user: {e}")
