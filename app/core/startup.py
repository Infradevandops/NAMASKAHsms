"""Startup initialization for the application."""
import os
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.core.logging import get_logger
from app.models.user import User
from app.utils.security import hash_password

logger = get_logger("startup")


def ensure_database_schema():
    """Ensure database has all required columns."""
    try:
        with engine.connect() as conn:
            # Add ALL missing columns from User model
            columns_to_add = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_sms_balance FLOAT DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_quota_used FLOAT DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_quota_reset_date TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'USD'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_id VARCHAR(50) DEFAULT 'payg'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS ban_reason VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_reason VARCHAR(500)",
            ]
            
            for sql in columns_to_add:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    logger.debug(f"Column may already exist: {e}")
            
            logger.info("Database schema verified")
    except Exception as e:
        logger.warning(f"Schema check failed: {e}")


def ensure_admin_user():
    """Ensure admin user exists on startup."""
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_password:
            logger.warning("ADMIN_PASSWORD not set in environment. Skipping admin user creation.")
            return

        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            # Update password and tier to ensure it's correct
            existing_admin.password_hash = hash_password(admin_password)
            existing_admin.is_admin = True
            existing_admin.email_verified = True
            existing_admin.subscription_tier = 'custom'  # Changed from 'turbo' to 'custom' (highest tier)
            existing_admin.credits = 10000.0
            existing_admin.free_verifications = 1000.0
            db.commit()
            logger.info("Admin user verified and updated with Turbo tier")
            return

        # Create admin user with Turbo tier access
        admin_user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            credits=10000.0,
            is_admin=True,
            email_verified=True,
            free_verifications=1000.0,
            subscription_tier='custom'  # Changed from 'turbo' to 'custom' (highest tier)
        )

        db.add(admin_user)
        db.commit()

        logger.info(f"Admin user created: {admin_email}")

    except IntegrityError as e:
        logger.warning(f"Admin user creation failed - user may already exist: {e}")
        db.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Database error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def run_startup_initialization():
    """Run all startup initialization tasks."""
    logger.info("Running startup initialization")

    try:
        ensure_database_schema()
        ensure_admin_user()
        logger.info("Startup initialization completed")
    except SQLAlchemyError as e:
        logger.error(f"Database error during startup initialization: {e}")
    except OSError as e:
        logger.error(f"Environment configuration error during startup: {e}")
    except (ImportError, AttributeError, TypeError) as e:
        logger.error(f"Configuration or import error during startup initialization: {e}")
    except Exception as e:
        logger.critical(f"Critical unexpected error during startup initialization: {e}")
        raise
