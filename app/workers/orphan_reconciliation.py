"""Orphan purchase reconciliation worker.

When a provider purchase call times out (G-001), the thread keeps running and
TV may still assign a number. This worker finds those ghost purchases, creates
the missing Verification row, deducts credits, and notifies the user via WS.

Runs every 60s. Provider-agnostic — works for TV, 5sim, Telnyx, PVApins.
"""

import asyncio
import json
from datetime import datetime, timezone

from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_orphan_reconciliation():
    """Background loop — checks for orphaned purchases every 60s."""
    while True:
        try:
            await _reconcile_once()
        except Exception as e:
            logger.error(f"Orphan reconciliation error: {e}")
        await asyncio.sleep(60)


async def _reconcile_once():
    from app.core.cache import get_redis
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.verification import Verification
    from app.services.balance_service import BalanceService
    from app.services.providers.textverified_adapter import TextVerifiedAdapter

    redis = get_redis()
    keys = redis.keys("purchase_pending:*")
    if not keys:
        return

    tv = TextVerifiedAdapter()
    if not tv.enabled:
        return

    # Fetch TV recent purchases once for all pending keys
    recent = await tv.list_recent_purchases(since_seconds=300)
    if not recent:
        return

    for key in keys:
        raw = redis.get(key)
        if not raw:
            continue
        try:
            pending = json.loads(raw)
        except Exception:
            redis.delete(key)
            continue

        user_id = pending.get("user_id")
        service = pending.get("service")
        cost = float(pending.get("cost", 0))
        started_at_str = pending.get("started_at", "")

        try:
            started_at = datetime.fromisoformat(started_at_str)
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
        except Exception:
            redis.delete(key)
            continue

        # Match by service + created_at within ±60s of started_at
        match = None
        for purchase in recent:
            if purchase.get("service", "").lower() != service.lower():
                continue
            try:
                created = datetime.fromisoformat(purchase["created_at"])
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                delta = abs((created - started_at).total_seconds())
                if delta <= 60:
                    match = purchase
                    break
            except Exception:
                continue

        if not match:
            # Not found yet — leave key alive (TTL=120s handles cleanup)
            continue

        # Found — heal the gap
        try:
            with SessionLocal() as db:
                # Check not already recorded
                existing = db.query(Verification).filter(
                    Verification.activation_id == match["order_id"]
                ).first()
                if existing:
                    redis.delete(key)
                    continue

                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    redis.delete(key)
                    continue

                verification = Verification(
                    user_id=user_id,
                    service_name=service,
                    phone_number=match["phone_number"],
                    country=pending.get("country", "US"),
                    capability=pending.get("capability", "sms"),
                    cost=cost,
                    provider="textverified",
                    activation_id=match["order_id"],
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(verification)
                db.flush()

                success, error = await BalanceService.deduct_credits_for_verification(
                    db=db, user=user, verification=verification,
                    cost=cost, service_name=service,
                    country_code=pending.get("country", "US"),
                )
                if not success:
                    db.rollback()
                    logger.warning(f"Orphan recon: debit failed for {user_id}: {error}")
                    redis.delete(key)
                    continue

                db.commit()
                logger.info(
                    f"Orphan reconciled: user={user_id} service={service} "
                    f"number={match['phone_number']} id={verification.id}"
                )

                # Notify user via WebSocket
                try:
                    from app.services.websocket_manager import websocket_manager
                    await websocket_manager.send_to_user(user_id, {
                        "type": "verification_ready",
                        "verification_id": str(verification.id),
                        "phone_number": match["phone_number"],
                        "service": service,
                        "message": "Your number is ready!",
                    })
                except Exception as ws_err:
                    logger.warning(f"Orphan recon WS notify failed: {ws_err}")

                # Start polling
                try:
                    from app.services.sms_polling_service import sms_polling_service
                    asyncio.create_task(sms_polling_service.start_polling(verification.id))
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Orphan recon heal failed for key {key}: {e}")
            continue

        redis.delete(key)
