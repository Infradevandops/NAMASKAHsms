"""Adaptive polling service that optimizes intervals based on metrics."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.models.verification import Verification

logger = get_logger(__name__)


class AdaptivePollingService:
    """Dynamically adjust polling intervals based on success metrics."""

    @staticmethod
    def get_optimal_interval(db: Session, service: str = None) -> int:
        """Calculate optimal polling interval based on recent metrics."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        query = db.query(Verification).filter(
            Verification.created_at >= cutoff,
            Verification.status == "completed"
        )

        if service:
            query = query.filter(Verification.service_name == service)

        verifications = query.all()

        if not verifications:
            return settings.sms_polling_initial_interval_seconds

        # Calculate average time to receive SMS
        polling_times = [
            (v.completed_at - v.created_at).total_seconds()
            for v in verifications if v.completed_at
        ]

        if not polling_times:
            return settings.sms_polling_initial_interval_seconds

        avg_time = sum(polling_times) / len(polling_times)

        # Optimize interval: use 1/3 of average time, min 5s, max 30s
        optimal = max(5, min(30, int(avg_time / 3)))

        logger.info(f"Optimal polling interval: {optimal}s (avg SMS time: {avg_time:.1f}s)")
        return optimal

    @staticmethod
    def should_increase_interval(db: Session, service: str = None) -> bool:
        """Check if polling interval should be increased (low success rate)."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        query = db.query(Verification).filter(
            Verification.created_at >= cutoff
        )

        if service:
            query = query.filter(Verification.service_name == service)

        verifications = query.all()

        if len(verifications) < 5:
            return False

        success_rate = sum(1 for v in verifications if v.status == "completed") / len(verifications)

        # If success rate < 70%, increase interval
        return success_rate < 0.70

    @staticmethod
    def should_decrease_interval(db: Session, service: str = None) -> bool:
        """Check if polling interval should be decreased (high success rate)."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        query = db.query(Verification).filter(
            Verification.created_at >= cutoff
        )

        if service:
            query = query.filter(Verification.service_name == service)

        verifications = query.all()

        if len(verifications) < 10:
            return False

        success_rate = sum(1 for v in verifications if v.status == "completed") / len(verifications)

        # If success rate > 95%, decrease interval
        return success_rate > 0.95

    @staticmethod
    def get_service_specific_interval(db: Session, service: str) -> int:
        """Get optimized interval for specific service."""
        base_interval = AdaptivePollingService.get_optimal_interval(db, service)

        if AdaptivePollingService.should_increase_interval(db, service):
            return min(base_interval + 5, 30)

        if AdaptivePollingService.should_decrease_interval(db, service):
            return max(base_interval - 2, 5)

        return base_interval
