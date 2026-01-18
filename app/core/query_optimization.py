"""Query optimization utilities - WITH ERROR HANDLING."""

from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.models.verification import Verification
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_user_verifications_optimized(db, user_id: str, limit: int = 100):
    """Get user verifications with eager loading."""
    try:
        return (
            db.query(Verification)
            .options(joinedload(Verification.user))
            .filter(Verification.user_id == user_id)
            .order_by(Verification.created_at.desc())
            .limit(limit)
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Query failed for user {user_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching verifications: {e}")
        return []


def get_verification_with_user(db, verification_id: str):
    """Get verification with user data in single query."""
    try:
        return (
            db.query(Verification)
            .options(joinedload(Verification.user))
            .filter(Verification.id == verification_id)
            .first()
        )
    except SQLAlchemyError as e:
        logger.error(f"Query failed for verification {verification_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching verification: {e}")
        return None


def get_user_with_verifications(db, user_id: str):
    """Get user with verification count."""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Query failed for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching user: {e}")
        return None
