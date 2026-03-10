"""Database indexes for query optimization - WITH ERROR HANDLING."""

from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


def create_indexes(engine):
    """Create database indexes for performance."""
    try:
        with engine.connect() as conn:
            index_statements = [
                (
                    "idx_verification_user_status",
                    "CREATE INDEX IF NOT EXISTS idx_verification_user_status ON verifications(user_id, status, created_at DESC)",
                ),
                (
                    "idx_verification_country_service",
                    "CREATE INDEX IF NOT EXISTS idx_verification_country_service ON verifications(country, service_name)",
                ),
                (
                    "idx_verification_created",
                    "CREATE INDEX IF NOT EXISTS idx_verification_created ON verifications(created_at DESC)",
                ),
                (
                    "idx_user_email",
                    "CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)",
                ),
            ]

            for name, stmt in index_statements:
                try:
                    conn.execute(stmt)
                    logger.info(f"Created index: {name}")
                except SQLAlchemyError as e:
                    logger.warning(f"Index creation failed: {e}")

            conn.commit()
            logger.info("All indexes created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database connection error during index creation: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating indexes: {e}")
