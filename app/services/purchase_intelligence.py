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
        provider: Optional[str] = None,
        country: Optional[str] = None,
        raw_sms_code: Optional[str] = None,
        latency_seconds: Optional[float] = None,
        provider_cost: Optional[float] = None,
        user_price: Optional[float] = None,
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
                        provider=provider,
                        country=country,
                        raw_sms_code=raw_sms_code,
                        latency_seconds=latency_seconds,
                        provider_cost=provider_cost,
                        user_price=user_price,
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
    async def update_sms_received(
        verification_id: str,
        sms_received: bool,
        raw_sms_code: Optional[str] = None,
        latency_seconds: Optional[float] = None,
        refund_reason: Optional[str] = None,
    ):
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
                        .values(
                            sms_received=sms_received,
                            raw_sms_code=raw_sms_code,
                            latency_seconds=latency_seconds,
                            refund_reason=refund_reason,
                        )
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
 
    @staticmethod
    async def get_live_health_score(
        service: str, country: str, provider: str
    ) -> float:
        """Calculate success rate for a provider+service+country in the last 60 minutes.
 
        Returns a float between 0.0 and 1.0.
        If no data exists, returns 1.0 (optimistic start).
        """
        cache_key = f"health:{provider}:{service}:{country}"
        cached_health = await cache.get(cache_key)
        if cached_health is not None:
            return float(cached_health)
 
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
 
        db = SessionLocal()
        try:
            # Query outcomes for this niche in the last hour
            outcomes = (
                db.query(PurchaseOutcome)
                .filter(
                    PurchaseOutcome.service == service,
                    PurchaseOutcome.country == country,
                    PurchaseOutcome.provider == provider,
                    PurchaseOutcome.created_at >= one_hour_ago,
                )
                .all()
            )
 
            if not outcomes:
                # Optimistic: No data means assume it's working
                await cache.set(cache_key, 1.0, 300)
                return 1.0
 
            # Success means we got a code. 
            # (In institutional grade, we ignore matched/mismatched for health, 
            # as that's an inventory issue, not a service failure)
            successes = sum(1 for o in outcomes if o.sms_received is True)
            total = len(outcomes)
 
            health_rate = successes / total
            await cache.set(cache_key, health_rate, 300)
            return health_rate
 
        except Exception as e:
            logger.error(f"Failed to calculate live health for {provider}: {e}")
            return 1.0
        finally:
            db.close()

    @staticmethod
    def get_provider_roi(db: Session, days: int = 30) -> Dict[str, Any]:
        """Calculate ROI and Margins per provider for routing prioritization."""
        from datetime import datetime, timedelta, timezone
        from app.models.purchase_outcome import PurchaseOutcome
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        outcomes = (
            db.query(PurchaseOutcome)
            .filter(PurchaseOutcome.created_at >= cutoff)
            .all()
        )

        stats = {}
        for o in outcomes:
            p = o.provider or "unknown"
            if p not in stats:
                stats[p] = {"cost": 0.0, "rev": 0.0, "refunds": 0.0}
            
            stats[p]["cost"] += (o.provider_cost or 0.0)
            stats[p]["rev"] += (o.user_price or 0.0)
            if o.is_refunded:
                stats[p]["refunds"] += (o.refund_amount or 0.0)

        roi_data = {}
        for p, s in stats.items():
            gross = s["rev"] - s["cost"]
            net = gross - s["refunds"]
            roi = (gross / s["cost"] * 100) if s["cost"] > 0 else 0.0
            roi_data[p] = {
                "roi_pct": round(roi, 2),
                "net_profit": round(net, 2),
                "efficiency_score": round(roi * (1 - (s["refunds"]/s["rev"] if s["rev"] > 0 else 0)), 2)
            }
        return roi_data

    @staticmethod
    def get_carrier_sentiment(db: Session, service: str, days: int = 14) -> Dict[str, float]:
        """Returns success rates per carrier for a specific service."""
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import func, Integer
        from app.models.purchase_outcome import PurchaseOutcome
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results = (
            db.query(
                PurchaseOutcome.assigned_carrier,
                func.count(PurchaseOutcome.id).label("total"),
                func.sum(func.cast(PurchaseOutcome.sms_received, Integer)).label("successes")
            )
            .filter(
                PurchaseOutcome.service == service,
                PurchaseOutcome.created_at >= cutoff,
                PurchaseOutcome.assigned_carrier.isnot(None),
                PurchaseOutcome.sms_received.isnot(None)
            )
            .group_by(PurchaseOutcome.assigned_carrier)
            .all()
        )

        return {r.assigned_carrier: round(r.successes / r.total, 2) for r in results if r.total > 0}
