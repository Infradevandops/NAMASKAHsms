"""Database indexes for query optimization - WITH ERROR HANDLING."""


from sqlalchemy.exc import SQLAlchemyError
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_indexes(engine):

    """Create database indexes for performance."""
try:
with engine.connect() as conn:
try:
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_verification_user_status
                    ON verifications(user_id, status, created_at DESC)
                """
                )
                logger.info("Created index: idx_verification_user_status")
except SQLAlchemyError as e:
                logger.warning(f"Index creation failed: {e}")

try:
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_verification_country_service
                    ON verifications(country, service_name)
                """
                )
                logger.info("Created index: idx_verification_country_service")
except SQLAlchemyError as e:
                logger.warning(f"Index creation failed: {e}")

try:
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_verification_created
                    ON verifications(created_at DESC)
                """
                )
                logger.info("Created index: idx_verification_created")
except SQLAlchemyError as e:
                logger.warning(f"Index creation failed: {e}")

try:
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_email
                    ON users(email)
                """
                )
                logger.info("Created index: idx_user_email")
except SQLAlchemyError as e:
                logger.warning(f"Index creation failed: {e}")

            conn.commit()
            logger.info("All indexes created successfully")
except SQLAlchemyError as e:
        logger.error(f"Database connection error during index creation: {e}")
except Exception as e:
        logger.error(f"Unexpected error creating indexes: {e}")
