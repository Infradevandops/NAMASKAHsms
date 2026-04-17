import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.unified_cache import cache
from app.models.purchase_outcome import PurchaseOutcome
from app.services.area_code_geo import NANPA_DATA

logger = logging.getLogger(__name__)


class AvailabilityScore(BaseModel):
    available: Optional[bool]
    confidence: float
    sample_size: int
    success_rate: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]


class PurchaseIntelligenceService:
    @staticmethod
    async def log_outcome(
        service: str,
        assigned_code: str,
        requested_code: Optional[str] = None,
        assigned_carrier: Optional[str] = None,
        carrier_type: Optional[str] = None,
        matched: Optional[bool] = None,
        user_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        selected_from_alternatives: Optional[bool] = False,
        original_request: Optional[str] = None,
    ):
        """Fire-and-forget logging of purchase outcome, enriched with geo data."""

        async def _log():
            try:
                assigned_city = None
                assigned_state = None
                if assigned_code in NANPA_DATA:
                    assigned_city = NANPA_DATA[assigned_code].get("major_city")
                    assigned_state = NANPA_DATA[assigned_code].get("state")

                now_utc = datetime.now(timezone.utc)

                db = SessionLocal()
                try:
                    outcome = PurchaseOutcome(
                        service=service,
                        requested_code=requested_code,
                        assigned_code=assigned_code,
                        assigned_carrier=assigned_carrier,
                        carrier_type=carrier_type,
                        assigned_city=assigned_city,
                        assigned_state=assigned_state,
                        matched=matched,
                        user_id=user_id,
                        verification_id=verification_id,
                        selected_from_alternatives=selected_from_alternatives,
                        original_request=original_request,
                        created_at=now_utc,
                        hour_utc=now_utc.hour,
                        day_of_week=now_utc.weekday(),
                    )
                    db.add(outcome)
                    db.commit()
                finally:
                    db.close()

                # Invalidate cache
                cache_key = f"acscore:{service}:{assigned_code}"
                await cache.delete(cache_key)
                if requested_code and requested_code != assigned_code:
                    cache_key2 = f"acscore:{service}:{requested_code}"
                    await cache.delete(cache_key2)

            except Exception as e:
                logger.error(f"Failed to log purchase outcome: {e}")

        # Run as a background task to be non-blocking
        asyncio.create_task(_log())

    @staticmethod
    async def update_sms_received(verification_id: str, sms_received: bool):
        """Called after polling completes."""
        if not verification_id:
            return

        async def _update():
            try:
                # Inside fire-and-forget, we must get a sync session
                db = SessionLocal()
                try:
                    stmt = (
                        update(PurchaseOutcome)
                        .where(PurchaseOutcome.verification_id == verification_id)
                        .values(sms_received=sms_received)
                    )
                    db.execute(stmt)
                    db.commit()
                finally:
                    db.close()
            except Exception as e:
                logger.error(
                    f"Failed to update sms_received for {verification_id}: {e}"
                )

        asyncio.create_task(_update())

    @staticmethod
    async def score_availability(service: str, area_code: str) -> AvailabilityScore:
        """Score availability for a service+area_code from the last 7 days of purchase history.

        Opens its own DB session so it can be called from anywhere (including TextVerifiedService)
        without needing a FastAPI-injected session.  Falls back to `unknown` gracefully on DB error.
        """
        cache_key = f"acscore:{service}:{area_code}"
        cached_score = await cache.get(cache_key)
        if cached_score:
            return AvailabilityScore(**cached_score)

        _UNKNOWN = AvailabilityScore(
            available=None,
            confidence=0.0,
            sample_size=0,
            success_rate=0.0,
            last_success=None,
            last_failure=None,
        )

        # Compute from last 7 days — open own session (matches log_outcome pattern)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

        db = SessionLocal()
        try:
            outcomes = (
                db.query(PurchaseOutcome)
                .filter(
                    PurchaseOutcome.service == service,
                    (
                        (PurchaseOutcome.assigned_code == area_code)
                        | (PurchaseOutcome.requested_code == area_code)
                    ),
                    PurchaseOutcome.created_at >= seven_days_ago,
                )
                .all()
            )
        except Exception as err:
            logger.error(f"score_availability DB query failed: {err}")
            return _UNKNOWN
        finally:
            db.close()

        if not outcomes:
            await cache.set(cache_key, _UNKNOWN.model_dump(mode="json"), 600)
            return _UNKNOWN

        successes = 0.0
        total_weight = 0.0
        last_s = None
        last_f = None

        for outcome in outcomes:
            # Success = this exact area code was actually assigned
            is_success = outcome.assigned_code == area_code

            created_at = outcome.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            # Recency weighting: outcomes in the last 2 hours count 3×
            weight = 3.0 if created_at >= two_hours_ago else 1.0
            total_weight += weight

            if is_success:
                successes += weight
                if not last_s or created_at > last_s:
                    last_s = created_at
            else:
                if not last_f or created_at > last_f:
                    last_f = created_at

        success_rate = successes / total_weight if total_weight > 0 else 0.0

        # Confidence tiers (from roadmap spec)
        sample_size = len(outcomes)
        if sample_size <= 2:
            confidence = 0.3
        elif sample_size <= 9:
            confidence = 0.6
        else:
            confidence = 0.9

        available = None
        if success_rate >= 0.6:
            available = True
        elif success_rate < 0.4:
            available = False

        # If there was a very recent failure after the last success, downgrade to unknown
        if (
            last_f
            and last_s
            and last_f > last_s
            and (datetime.now(timezone.utc) - last_f) < timedelta(hours=1)
        ):
            if available is True and confidence <= 0.6:
                available = None

        score = AvailabilityScore(
            available=available,
            confidence=confidence,
            sample_size=sample_size,
            success_rate=success_rate,
            last_success=last_s,
            last_failure=last_f,
        )

        await cache.set(cache_key, score.model_dump(mode="json"), 600)
        return score
