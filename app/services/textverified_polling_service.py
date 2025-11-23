"""SMS polling service for TextVerified verification updates."""
import asyncio
from datetime import datetime, timezone
from typing import Dict

from app.core.database import SessionLocal

logger = get_logger(__name__)


class TextVerifiedPollingService:
    """Polling service for TextVerified SMS verifications."""

    def __init__(self):
        self.textverified = provider_manager.get_provider("textverified")
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False

    async def start_polling(self, verification_id: str, activation_id: str):
        """Start polling for SMS for a specific verification."""
        if verification_id in self.polling_tasks:
            return  # Already polling

        task = asyncio.create_task(
            self._poll_verification(verification_id, activation_id)
        )
        self.polling_tasks[verification_id] = task
        logger.info(f"Started TextVerified polling for verification {verification_id}")

    async def stop_polling(self, verification_id: str):
        """Stop polling for a specific verification."""
        if verification_id in self.polling_tasks:
            task = self.polling_tasks.pop(verification_id)
            task.cancel()
            logger.info(f"Stopped TextVerified polling for verification {verification_id}")

    async def _poll_verification(self, verification_id: str, activation_id: str):
        """Poll TextVerified for SMS updates."""
        max_attempts = 120  # 10 minutes with 5 - second intervals
        attempt = 0

        while attempt < max_attempts:
            try:
                # Get database session
                db = SessionLocal()

                # Check if verification still exists and is pending
                verification = db.query(Verification).filter(
                    Verification.id == verification_id
                ).first()

                if not verification or verification.status != "pending":
                    logger.info(f"Verification {verification_id} no longer pending, stopping poll")
                    break

                # Check TextVerified for SMS
                try:
                    sms_code = await self.textverified.get_sms(activation_id)
                except Exception as e:
                    logger.warning(f"TextVerified SMS check failed for {activation_id}: {str(e)}")
                    attempt += 1
                    await asyncio.sleep(5)
                    continue  # Skip this iteration

                if sms_code:
                    # SMS received, update verification
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)

                    # Store SMS code
                    if hasattr(verification, 'sms_code'):
                        verification.sms_code = sms_code
                    if hasattr(verification, 'sms_text'):
                        verification.sms_text = f"Verification code: {sms_code}"

                    db.commit()
                    logger.info(f"SMS received for verification {verification_id}")
                    break

                attempt += 1
                await asyncio.sleep(5)  # Wait 5 seconds before next poll

            except Exception as e:
                logger.error(f"Error polling TextVerified for {verification_id}: {str(e)}")
                attempt += 1
                await asyncio.sleep(5)
                continue
            finally:
                try:
                    db.close()
                except Exception:
                    pass

        # Remove from polling tasks
        self.polling_tasks.pop(verification_id, None)
        logger.info(f"Finished polling for verification {verification_id}")

    async def start(self):
        """Start the polling service."""
        self.is_running = True
        logger.info("TextVerified polling service started")

    async def stop(self):
        """Stop the polling service and cancel all tasks."""
        self.is_running = False
        for task in self.polling_tasks.values():
            task.cancel()
        self.polling_tasks.clear()
        logger.info("TextVerified polling service stopped")


# Global instance
textverified_polling_service = TextVerifiedPollingService()
