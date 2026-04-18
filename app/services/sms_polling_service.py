"""SMS polling service — TextVerified only."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models import Verification
from app.services.adaptive_polling import AdaptivePollingService
from app.services.auto_refund_service import AutoRefundService

from app.services.notification_dispatcher import NotificationDispatcher
from app.services.notification_service import NotificationService
from app.services.purchase_intelligence import PurchaseIntelligenceService
from app.services.refund_policy_enforcer import refund_policy_enforcer
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


class SMSPollingService:

    def __init__(self):
        self.textverified = TextVerifiedService()
        self.adaptive = AdaptivePollingService()
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False

    async def start_polling(self, verification_id: str, phone_number: str = None):
        """Start polling for SMS for a specific verification."""
        if verification_id in self.polling_tasks:
            return
        task = asyncio.create_task(self._poll_verification(verification_id))
        self.polling_tasks[verification_id] = task
        logger.info(f"Started polling for verification {verification_id}")

    async def stop_polling(self, verification_id: str):
        """Stop polling for a specific verification."""
        if verification_id in self.polling_tasks:
            task = self.polling_tasks.pop(verification_id)
            task.cancel()
            logger.info(f"Stopped polling for verification {verification_id}")

    async def _poll_verification(self, verification_id: str):
        """Poll provider for SMS using provider-specific method."""
        db = None
        try:
            db = SessionLocal()
            verification = (
                db.query(Verification)
                .filter(Verification.id == verification_id)
                .first()
            )

            if not verification or verification.status != "pending":
                logger.info(
                    f"Verification {verification_id} no longer pending, stopping poll"
                )
                return

            if not verification.activation_id:
                logger.warning(
                    f"No activation_id for verification {verification_id}, stopping poll"
                )
                return

            # Calculate timeout
            timeout_seconds = settings.sms_polling_max_minutes * 60
            if hasattr(verification, "ends_at") and verification.ends_at:
                ends_at = verification.ends_at
                if ends_at.tzinfo is None:
                    ends_at = ends_at.replace(tzinfo=timezone.utc)
                remaining = (ends_at - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    timeout_seconds = min(remaining, timeout_seconds)

            # Dispatch by provider
            provider = getattr(verification, "provider", "textverified")
            if provider == "textverified":
                await self._poll_textverified(verification, db, timeout_seconds)
            elif provider == "telnyx":
                await self._poll_telnyx(verification, db, timeout_seconds)
            elif provider == "5sim":
                await self._poll_fivesim(verification, db, timeout_seconds)
            elif provider == "pvapins":
                await self._poll_pvapins(verification, db, timeout_seconds)
            else:
                logger.warning(
                    f"Unknown provider '{provider}' for verification {verification_id}, "
                    f"handling as timeout"
                )
                await self._handle_timeout(verification, db, reason="sms_timeout")

        except asyncio.CancelledError:
            logger.info(f"Polling cancelled for verification {verification_id}")
        except Exception as e:
            logger.error(
                f"Unexpected polling error for {verification_id}: {str(e)}",
                exc_info=True,
            )
        finally:
            if db:
                db.close()
            if verification_id in self.polling_tasks:
                self.polling_tasks.pop(verification_id)

    async def _poll_textverified(self, verification, db, timeout_seconds: float):
        """Poll TextVerified using standard sms.incoming() method."""
        tv_details = await self.textverified.get_verification_details(
            verification.activation_id
        )

        if not tv_details:
            logger.warning(
                f"Could not get TV details for {verification.activation_id}, "
                f"falling back to legacy polling"
            )
            await self._poll_legacy(verification, db, timeout_seconds)
            return

        # Build minimal object for sms.incoming()
        class _TVVerif:
            def __init__(self, d, _created_at, _service_name="unknown"):
                self.number = d["number"]
                self.created_at = _created_at
                self.id = d["id"]
                self.ends_at = d.get("ends_at")
                self.service_name = _service_name

        tv_obj = _TVVerif(
            tv_details, verification.created_at, verification.service_name
        )

        # Phase 11: Late-binding carrier enrichment
        if tv_details.get("carrier"):
            asyncio.create_task(
                PurchaseIntelligenceService.enrich_outcome_carrier(
                    verification.id, tv_details.get("carrier")
                )
            )

        logger.info(
            f"Polling {verification.id} via sms.incoming() "
            f"(timeout={timeout_seconds:.0f}s)"
        )

        # Notify user we're still waiting
        asyncio.create_task(
            self._notify_waiting(verification.user_id, verification.service_name)
        )

        # Standard TextVerified poll
        result = await self.textverified.poll_sms_standard(
            tv_obj, timeout_seconds=timeout_seconds
        )

        # Reload verification
        db.expire(verification)
        verification = (
            db.query(Verification).filter(Verification.id == verification.id).first()
        )
        if not verification or verification.status != "pending":
            return

        if result.get("success"):
            # Prepare metadata for completion
            code = result.get("code", "")
            text = result.get("sms", "")
            transcription = result.get("transcription")
            audio_url = result.get("audio_url")

            # Fallback for voice: if no code but have transcription, use transcription
            if verification.capability == "voice" and not code and transcription:
                code = "VOICE_RECV"
                text = transcription

            if code:
                await self._complete_verification(
                    verification,
                    db,
                    text,
                    code,
                    transcription=transcription,
                    audio_url=audio_url,
                )
                return
            elif verification.capability == "voice" and audio_url:
                # Institutional Mastery: Partial success - mark as transcribing and continue
                from app.services.verification_status_service import (
                    mark_verification_transcribing,
                )

                await mark_verification_transcribing(
                    db, verification, audio_url=audio_url
                )
                logger.info(f"Verification {verification.id} marked as TRANSCRIBING")
                # We need to re-poll because we haven't reached terminal success
                await self._poll_textverified(verification, db, timeout_seconds - 30)
                return
            else:
                logger.warning(f"Poll success but no usable code for {verification.id}")
                await self._handle_timeout(verification, db, reason="sms_timeout")
        else:
            await self._handle_timeout(verification, db, reason="sms_timeout")

    async def _poll_telnyx(self, verification, db, timeout_seconds: float):
        """Poll Telnyx for SMS with adaptive backoff."""
        from app.services.providers.telnyx_adapter import TelnyxAdapter

        adapter = TelnyxAdapter()
        logger.info(
            f"Polling {verification.id} via Telnyx (timeout={timeout_seconds:.0f}s)"
        )

        start_time = datetime.now(timezone.utc)
        while (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() < timeout_seconds:
            # Phase 12: Adaptive Intelligence
            delay = self.adaptive.get_optimal_interval(
                db, service=verification.service_name
            )

            try:
                messages = await adapter.check_messages(verification.activation_id)
                if messages:
                    msg = messages[-1]
                    await self._complete_verification(
                        verification, db, msg.text, msg.code
                    )
                    return
            except Exception as e:
                logger.warning(f"Telnyx polling error for {verification.id}: {e}")

            await asyncio.sleep(delay)

        await self._handle_timeout(verification, db, reason="sms_timeout")

    async def _poll_fivesim(self, verification, db, timeout_seconds: float):
        """Poll 5sim for SMS with adaptive backoff."""
        from app.services.providers.fivesim_adapter import FiveSimAdapter

        adapter = FiveSimAdapter()
        logger.info(
            f"Polling {verification.id} via 5sim (timeout={timeout_seconds:.0f}s)"
        )

        start_time = datetime.now(timezone.utc)
        while (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() < timeout_seconds:
            # Phase 12: Adaptive Intelligence
            delay = self.adaptive.get_optimal_interval(
                db, service=verification.service_name
            )

            try:
                messages = await adapter.check_messages(verification.activation_id)
                if messages:
                    msg = messages[-1]
                    await self._complete_verification(
                        verification, db, msg.text, msg.code
                    )
                    return
            except Exception as e:
                logger.warning(f"5sim polling error for {verification.id}: {e}")

            await asyncio.sleep(delay)

        await self._handle_timeout(verification, db, reason="sms_timeout")

    async def _poll_pvapins(self, verification, db, timeout_seconds: float):
        """Poll PVApins for SMS."""
        logger.info(f"Polling {verification.id} via PVApins (fallback to legacy)")
        await self._poll_legacy(verification, db, timeout_seconds)

    async def _complete_verification(
        self,
        verification,
        db,
        sms_text: str,
        sms_code: str,
        transcription: Optional[str] = None,
        audio_url: Optional[str] = None,
    ):
        """Shared success logic after SMS/Voice is received."""
        # Reload verification to avoid stale state
        db.expire(verification)
        v = db.query(Verification).filter(Verification.id == verification.id).first()
        if not v or v.status != "pending":
            return

        from app.services.verification_status_service import mark_sms_code_received

        await mark_sms_code_received(
            db, v, sms_code, sms_text, transcription=transcription, audio_url=audio_url
        )

        # Instrumentation
        latency = None
        if v.created_at:
            created_at = (
                v.created_at.replace(tzinfo=timezone.utc)
                if v.created_at.tzinfo is None
                else v.created_at
            )
            latency = int((v.completed_at - created_at).total_seconds())

        asyncio.create_task(
            PurchaseIntelligenceService.update_sms_received(
                v.id, True, raw_sms_code=v.sms_code, latency_seconds=latency
            )
        )

        # Notify & Forward
        try:
            from app.api.core.forwarding import forward_sms_message

            asyncio.create_task(
                forward_sms_message(
                    user_id=v.user_id,
                    sms_data={
                        "message": v.sms_text or "",
                        "sms_code": v.sms_code or "",
                        "phone_number": v.phone_number,
                        "service": v.service_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    db=db,
                )
            )
        except Exception:
            pass

        try:
            dispatcher = NotificationDispatcher(db)
            dispatcher.on_sms_received(v)
        except Exception:
            pass

        logger.info(
            f"✅ SMS received for {v.id} (provider={v.provider}) — code={v.sms_code}"
        )

    async def _handle_timeout(
        self, verification: Verification, db, reason: str = "timeout"
    ):
        from app.core.constants import FailureReason
        from app.services.verification_status_service import mark_verification_failed

        # Calculate reason
        failure_reason = FailureReason.SMS_NOT_DELIVERED
        if reason == "timeout":
            failure_reason = FailureReason.PROVIDER_TIMEOUT

        await mark_verification_failed(
            db,
            verification,
            reason=failure_reason,
            error_message=f"SMS not received within timeframe: {reason}",
            refund_eligible=True,
        )

        # Phase 10: Categorization
        outcome_category = "NETWORK"

        # Also report to provider for their refund (Phase 10 Recoup Tracking)
        provider = getattr(verification, "provider", "textverified")
        provider_refunded = False

        try:
            if provider == "textverified":
                provider_refunded = await self.textverified.report_verification(
                    verification.activation_id
                )
            elif provider == "telnyx":
                from app.services.providers.telnyx_adapter import TelnyxAdapter

                provider_refunded = await TelnyxAdapter().report_failed(
                    verification.activation_id
                )
            elif provider == "5sim":
                from app.services.providers.fivesim_adapter import FiveSimAdapter

                provider_refunded = await FiveSimAdapter().report_failed(
                    verification.activation_id
                )
        except Exception as e:
            logger.warning(f"Failed to recoup from provider {provider}: {e}")

        if provider_refunded:
            logger.info(f"✅ RECOUPED: {verification.id} from {provider}")
        else:
            logger.warning(
                f"⚠️ RECOUP FAILED: {verification.id} from {provider} (Potential leakage)"
            )

        # --- PHASE 2 & 10 INSTRUMENTATION ---
        asyncio.create_task(
            PurchaseIntelligenceService.update_sms_received(
                verification.id,
                False,
                refund_reason=reason,
                outcome_category=outcome_category,
                provider_refunded=provider_refunded,
            )
        )

        logger.info(f"Verification {verification.id} timed out")

    async def _notify_waiting(self, user_id: str, service_name: str):
        """Send 'still waiting' notification after 20 seconds."""
        await asyncio.sleep(20)
        db = None
        try:
            db = SessionLocal()
            notif_service = NotificationService(db)
            notif_service.create_notification(
                user_id=user_id,
                notification_type="verification_progress",
                title="⏳ Still Waiting",
                message=f"Waiting for SMS code for {service_name}...",
            )
        except Exception:
            pass
        finally:
            if db:
                db.close()

    async def _poll_legacy(
        self, verification: Verification, db, timeout_seconds: float
    ):
        """Legacy polling fallback with progressive delay."""
        import re

        start_time = datetime.now(timezone.utc)
        delay = 2.0
        while (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() < timeout_seconds:
            if verification.status != "pending":
                break

            try:
                sms_data = await self.textverified.check_sms(
                    verification.activation_id,
                    created_after=verification.created_at,
                )
                if sms_data and sms_data.get("messages"):
                    latest = sms_data["messages"][-1]
                    sms_text = (
                        latest if isinstance(latest, str) else latest.get("text", "")
                    )
                    pre_parsed = (
                        latest.get("code", "") if isinstance(latest, dict) else ""
                    )

                    if pre_parsed:
                        extracted_code = pre_parsed
                    else:
                        hyphen = re.findall(r"\b(\d{3}-\d{3})\b", sms_text)
                        plain = re.findall(r"\b(\d{4,8})\b", sms_text)
                        extracted_code = (
                            hyphen[-1].replace("-", "")
                            if hyphen
                            else plain[-1] if plain else None
                        )

                    if extracted_code:
                        await self._complete_verification(
                            verification, db, sms_text, extracted_code
                        )
                        return
            except Exception as e:
                logger.warning(f"Legacy check_sms failed: {e}")

            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 10.0)

        await self._handle_timeout(verification, db, reason="sms_timeout")

    async def start_background_service(self):
        """Start the background polling service."""
        self.is_running = True
        logger.info("SMS polling service started")

        while self.is_running:
            db = None
            try:
                db = SessionLocal()
                pending = (
                    db.query(Verification)
                    .filter(Verification.status == "pending")
                    .all()
                )
                for v in pending:
                    if v.id not in self.polling_tasks:
                        await self.start_polling(v.id, v.phone_number)
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
