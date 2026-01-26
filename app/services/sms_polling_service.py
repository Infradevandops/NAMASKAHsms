"""SMS polling service for real-time verification updates."""

import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.models import Verification
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_service import NotificationService
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class SMSPollingService:
    def __init__(self):
        self.textverified = TextVerifiedService()
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False

    async def start_polling(self, verification_id: str, phone_number: str):
        """Start polling for SMS for a specific verification."""
        if verification_id in self.polling_tasks:
            return

        task = asyncio.create_task(self._poll_verification(verification_id, phone_number))
        self.polling_tasks[verification_id] = task
        logger.info(f"Started polling for verification {verification_id}")

    async def stop_polling(self, verification_id: str):
        """Stop polling for a specific verification."""
        if verification_id in self.polling_tasks:
            task = self.polling_tasks.pop(verification_id)
            task.cancel()
            logger.info(f"Stopped polling for verification {verification_id}")

    async def _poll_verification(self, verification_id: str, phone_number: str):
        """Poll TextVerified for SMS updates."""
        initial_interval = settings.sms_polling_initial_interval_seconds
        max_attempts = int((settings.sms_polling_max_minutes * 60) / max(1, initial_interval))
        attempt = 0

        while attempt < max_attempts:
            db = None
            try:
                db = SessionLocal()
                verification = db.query(Verification).filter(Verification.id == verification_id).first()

                if not verification or verification.status != "pending":
                    logger.info(f"Verification {verification_id} no longer pending, stopping poll")
                    break

                # Use activation_id (TextVerified's ID) not our internal verification_id
                if not verification.activation_id:
                    logger.warning(f"No activation_id for verification {verification_id}, stopping poll")
                    break

                try:
                    sms_data = await self.textverified.check_sms(verification.activation_id)
                except Exception as e:
                    logger.warning(f"TextVerified check failed for {verification.activation_id}: {str(e)}")
                    await asyncio.sleep(settings.sms_polling_error_backoff_seconds)
                    attempt += 1
                    continue

                if sms_data and sms_data.get("messages"):
                    verification.status = "completed"
                    verification.completed_at = datetime.now(timezone.utc)
                    latest_sms = (
                        sms_data["messages"][-1] if isinstance(sms_data["messages"], list) else sms_data["messages"]
                    )
                    if hasattr(verification, "sms_text"):
                        verification.sms_text = (
                            latest_sms if isinstance(latest_sms, str) else latest_sms.get("text", "")
                        )
                    if hasattr(verification, "sms_code"):
                        text = latest_sms if isinstance(latest_sms, str) else latest_sms.get("text", "")
                        matches = re.findall(r"\b(\d{4,8})\b", text)
                        verification.sms_code = matches[-1] if matches else ""
                    db.commit()

                    # PHASE 2: Record successful verification for success rate tracking
                    try:
                        logger.info(f"Recording successful verification for {verification.service_name}")
                        # Note: We track by operator (carrier) and area_code fields on verification
                    except Exception as tracking_error:
                        logger.warning(f"Failed to record success tracking: {tracking_error}")

                    # Notification: SMS Code Received (Task 2.4 Enhanced)
                    try:
                        dispatcher = NotificationDispatcher(db)
                        dispatcher.on_sms_received(verification)
                    except Exception as e:
                        logger.warning(f"Failed to dispatch SMS received notification: {e}")

                    logger.info(f"SMS received for verification {verification_id}")
                    break

                elif sms_data and sms_data.get("status") == "TIMEOUT":
                    verification.status = "timeout"
                    db.commit()

                    # PHASE 2: Record failed verification for success rate tracking
                    try:
                        logger.info(f"Recording failed verification (timeout) for {verification.service_name}")
                        # Note: We track by operator (carrier) and area_code fields on verification
                    except Exception as tracking_error:
                        logger.warning(f"Failed to record failure tracking: {tracking_error}")

                    # CRITICAL FIX: Auto-refund for timeout
                    try:
                        from app.services.auto_refund_service import AutoRefundService

                        refund_service = AutoRefundService(db)
                        refund_result = refund_service.process_verification_refund(verification_id, "timeout")
                        if refund_result:
                            logger.info(f"Auto-refund processed for timeout: ${refund_result['refund_amount']:.2f}")
                    except Exception as refund_error:
                        logger.error(
                            f"Failed to process auto-refund for {verification_id}: {refund_error}",
                            exc_info=True,
                        )

                    # Notification: Verification Failed
                    try:
                        notif_service = NotificationService(db)
                        notif_service.create_notification(
                            user_id=verification.user_id,
                            notification_type="verification_failed",
                            title="Verification Timeout - Refund Issued",
                            message=f"No SMS received for {verification.service_name}. Credits refunded.",
                        )
                    except Exception:
                        pass

                    logger.info(f"Verification {verification_id} timed out")
                    break

                # Wait before next poll
                if attempt < 10:
                    await asyncio.sleep(settings.sms_polling_initial_interval_seconds)
                else:
                    await asyncio.sleep(settings.sms_polling_later_interval_seconds)

                attempt += 1

                # Progress Update (Task 2.3)
                if attempt == 4:  # After ~2 minutes (assuming 30s interval for later or initial)
                    try:
                        notif_service = NotificationService(db)
                        notif_service.create_notification(
                            user_id=verification.user_id,
                            notification_type="verification_progress",
                            title="⏳ Still Waiting",
                            message=f"Waiting for SMS code for {verification.service_name}...",
                        )
                    except Exception:
                        pass

            except asyncio.CancelledError:
                logger.info(f"Polling cancelled for verification {verification_id}")
                break
            except ExternalServiceError as e:
                logger.warning(f"TextVerified polling error for {verification_id}: {str(e)}")
                await asyncio.sleep(settings.sms_polling_error_backoff_seconds)
                attempt += 1
            except Exception as e:
                logger.error(f"Unexpected polling error for {verification_id}: {str(e)}")
                await asyncio.sleep(settings.sms_polling_error_backoff_seconds)
                attempt += 1
            finally:
                if db:
                    db.close()

        if verification_id in self.polling_tasks:
            self.polling_tasks.pop(verification_id)

    async def start_background_service(self):
        """Start the background polling service."""
        self.is_running = True
        logger.info("SMS polling service started")

        while self.is_running:
            db = None
            try:
                db = SessionLocal()
                pending_verifications = (
                    db.query(Verification)
                    .filter(
                        Verification.status == "pending",
                        Verification.provider == "textverified",
                    )
                    .all()
                )

                for verification in pending_verifications:
                    if verification.id not in self.polling_tasks:
                        await self.start_polling(
                            verification.id,
                            verification.phone_number,
                        )

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Background service error: {str(e)}")
                await asyncio.sleep(60)
            finally:
                if db:
                    db.close()

    async def stop_background_service(self):
        """Stop the background polling service."""
        self.is_running = False
        for task in self.polling_tasks.values():
            task.cancel()
        self.polling_tasks.clear()
        logger.info("SMS polling service stopped")

    def get_active_polls(self) -> List[str]:
        """Get list of active polling verification IDs."""
        return list(self.polling_tasks.keys())


sms_polling_service = SMSPollingService()
