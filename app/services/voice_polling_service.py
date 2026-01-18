"""Voice Polling Service - Production Hardened"""

from app.core.logging import get_logger
from app.core.database import get_db
from app.core.config import get_settings
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService
from app.services.notification_service import NotificationService
import asyncio
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = get_logger("voice_polling")
settings = get_settings()


@contextmanager
def get_db_session():
    """Context manager for safe DB session handling"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


class VoicePollingService:
    def __init__(self):
        self.tv_service = TextVerifiedService()
        self.running = False

    async def start_background_service(self):
        """Start polling for voice codes"""
        self.running = True
        logger.info("Voice polling service started")

        while self.running:
            try:
                await self.poll_voice_verifications()
                await asyncio.sleep(settings.voice_polling_interval_seconds)
            except Exception as e:
                logger.error(f"Voice polling error: {e}")
                await asyncio.sleep(settings.sms_polling_error_backoff_seconds)

    async def stop_background_service(self):
        """Stop polling"""
        self.running = False
        logger.info("Voice polling service stopped")

    async def poll_voice_verifications(self):
        """Poll pending voice verifications with retry logic"""
        with get_db_session() as db:
            try:
                timeout_threshold = datetime.now() - timedelta(
                    minutes=settings.voice_polling_timeout_minutes
                )
                pending = (
                    db.query(Verification)
                    .filter(
                        Verification.capability == "voice",
                        Verification.status == "pending",
                        Verification.created_at > timeout_threshold,
                    )
                    .all()
                )

                for verification in pending:
                    await self._poll_single_verification(verification, db)

            except Exception as e:
                logger.error(f"Error in poll_voice_verifications: {e}")

    async def _poll_single_verification(self, verification, db):
        """Poll single verification with error handling"""
        try:
            # Retry logic for TextVerified API
            result = None
            for attempt in range(settings.voice_max_retry_attempts):
                try:
                    result = self.tv_service.client.verifications.get(verification.activation_id)
                    break
                except Exception as e:
                    if attempt == settings.voice_max_retry_attempts - 1:
                        logger.error(
                            f"Failed to poll voice verification {verification.id} after {settings.voice_max_retry_attempts} attempts: {e}"
                        )
                        return
                    await asyncio.sleep(2**attempt)  # Exponential backoff

            if not result:
                return

            if result.code:
                verification.sms_code = result.code
                verification.status = "completed"
                db.commit()

                # Safe notification - won't break verification flow
                try:
                    notification_service = NotificationService(db)
                    notification_service.create_notification(
                        user_id=verification.user_id,
                        title="Voice Code Received",
                        message=f"Code: {result.code} for {verification.service_name}",
                        type="verification_complete",
                    )
                except Exception as notif_error:
                    logger.warning(
                        f"Notification failed for voice verification {verification.id}: {notif_error}"
                    )

                logger.info(f"Voice code received: {verification.id}")

            elif (datetime.now() - verification.created_at).seconds > (
                settings.voice_polling_timeout_minutes * 60
            ):
                verification.status = "failed"
                db.commit()

                try:
                    notification_service = NotificationService(db)
                    notification_service.create_notification(
                        user_id=verification.user_id,
                        title="Voice Verification Timeout",
                        message=f"No code received for {verification.service_name}",
                        type="verification_failed",
                    )
                except Exception as notif_error:
                    logger.warning(
                        f"Notification failed for voice timeout {verification.id}: {notif_error}"
                    )

                logger.warning(f"Voice verification timeout: {verification.id}")

        except Exception as e:
            logger.error(f"Error polling voice verification {verification.id}: {e}")


voice_polling_service = VoicePollingService()
