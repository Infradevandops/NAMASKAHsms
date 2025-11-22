"""Startup initialization for the application."""
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.user import User
from app.utils.security import hash_password

logger = get_logger("startup")


def ensure_admin_user():
    """Ensure admin user exists on startup."""
    db = SessionLocal()
    try:
        admin_email = "admin@namaskah.app"
        admin_password = "NamaskahAdmin2024!"

        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            logger.info("Admin user already exists")
            return

        # Create admin user
        admin_user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            credits=1000.0,
            is_admin=True,
            email_verified=True,
            free_verifications=100.0
        )

        db.add(admin_user)
        db.commit()

        logger.info(f"Admin user created: {admin_email}")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()


def run_startup_initialization():
    """Run all startup initialization tasks."""
    logger.info("Running startup initialization")

    try:
        ensure_admin_user()
        logger.info("Startup initialization completed")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
