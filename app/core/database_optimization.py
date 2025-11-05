"""Database optimization utilities for task 12.1."""
from sqlalchemy import Index, text
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification


def create_database_indexes(engine):
    """Create optimized database indexes."""

    # User table indexes
    Index("idx_user_email", User.email, unique=True)
    Index("idx_user_referral_code", User.referral_code)
    Index("idx_user_created_at", User.created_at)
    Index("idx_user_is_admin", User.is_admin)

    # Verification table indexes
    Index("idx_verification_user_id", Verification.user_id)
    Index("idx_verification_status", Verification.status)
    Index("idx_verification_service_name", Verification.service_name)
    Index("idx_verification_created_at", Verification.created_at)

    Index("idx_verification_user_status", Verification.user_id, Verification.status)

    # Transaction table indexes
    Index("idx_transaction_user_id", Transaction.user_id)
    Index("idx_transaction_type", Transaction.type)
    Index("idx_transaction_created_at", Transaction.created_at)
    Index("idx_transaction_user_type", Transaction.user_id, Transaction.type)

    # Create all indexes
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_user_referral_code ON users(referral_code);
            CREATE INDEX IF NOT EXISTS idx_user_created_at ON users(created_at);
            CREATE INDEX IF NOT EXISTS idx_verification_user_id ON verifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_verification_status ON verifications(status);
            CREATE INDEX IF NOT EXISTS idx_verification_created_at ON verifications(created_at);
            CREATE INDEX IF NOT EXISTS idx_transaction_user_id ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transaction_created_at ON transactions(created_at);
        """
            )
        )
        conn.commit()


class QueryOptimizer:
    """Query optimization utilities."""

    @staticmethod
    def get_user_verifications_optimized(db: Session, user_id: str, limit: int = 50):
        """Optimized query for user verifications."""
        return (
            db.query(Verification)
            .filter(Verification.user_id == user_id)
            .order_by(Verification.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_transactions_optimized(db: Session, user_id: str, limit: int = 50):
        """Optimized query for user transactions."""
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_verification_stats_optimized(db: Session, user_id: str):
        """Optimized query for verification statistics."""
        return db.execute(
            text(
                """
            SELECT 
                status,
                COUNT(*) as count,
                SUM(cost) as total_cost
            FROM verifications 
            WHERE user_id = :user_id 
            GROUP BY status
        """
            ),
            {"user_id": user_id},
        ).fetchall()


def configure_connection_pool():
    """Configure database connection pooling."""
    # Connection pool is configured in engine creation
    # This function documents the recommended settings
    pool_settings = {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }
    return pool_settings
