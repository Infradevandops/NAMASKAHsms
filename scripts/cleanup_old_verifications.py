#!/usr/bin/env python3
"""Clean up old verifications to stop polling spam."""


from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.verification import Verification

logger = get_logger(__name__)


def cleanup_old_verifications(hours=1):

    """Delete verifications older than specified hours."""
    db = SessionLocal()
try:
        old_time = datetime.utcnow() - timedelta(hours=hours)

        # Find old verifications
        old_verifications = (
            db.query(Verification).filter(Verification.created_at < old_time).all()
        )

        count = len(old_verifications)

if count == 0:
            logger.info("No old verifications to clean up")
            return 0

        # Delete them
        db.query(Verification).filter(Verification.created_at < old_time).delete()

        db.commit()
        logger.info(f"Cleaned up {count} old verifications")
        return count

except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
        return 0
finally:
        db.close()


if __name__ == "__main__":
    print("Cleaning up old verifications...")
    count = cleanup_old_verifications(hours=1)
    print(f"✅ Cleaned up {count} old verifications")