"""Service stock availability monitor.

Uses the existing TextVerified services cache (tv:services_list) to derive
real-time stock status. price=null means out of stock on TextVerified.
Stores a lightweight availability map in Redis for fast frontend reads.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core.logging import get_logger
from app.core.unified_cache import cache

logger = get_logger(__name__)

_STOCK_CACHE_KEY = "services:stock"
_STOCK_CACHE_TTL = 120  # 2 minutes — proactive live handshake with TV
_TV_SERVICES_KEY = "tv:services_list"
_OUTCOME_TTL = 1800  # 30 min — failed service stays red long enough to matter


async def record_purchase_outcome(service_slug: str, success: bool) -> None:
    """Record a real purchase outcome to correct stale price-based availability."""
    try:
        key = f"services:outcome:{service_slug.lower()}"
        await cache.set(
            key,
            {"available": success, "ts": datetime.now(timezone.utc).isoformat()},
            _OUTCOME_TTL,
        )
    except Exception as e:
        logger.warning(f"Failed to record purchase outcome for {service_slug}: {e}")


async def get_purchase_outcome(service_slug: str) -> Optional[bool]:
    """Return last known purchase outcome, or None if no recent data."""
    try:
        data = await cache.get(f"services:outcome:{service_slug.lower()}")
        return data["available"] if data else None
    except Exception:
        return None


async def build_stock_map() -> Dict[str, dict]:
    """Build availability map from cached TextVerified services list.

    Uses price > 0 as the availability signal (TV's only reliable stock indicator).
    Purchase outcomes only override for services that have a price (i.e. were available).
    Skips per-service Redis calls for null-price services to avoid 2351-call loops.
    """
    try:
        services = await cache.get(_TV_SERVICES_KEY)
        if not services:
            return {}

        # Only fetch outcomes for priced services — no point checking outcomes
        # for services with null price (they're unavailable regardless)
        priced_slugs = []
        stock_map = {}
        for svc in services:
            slug = (svc.get("id") or svc.get("name") or "").lower().strip()
            if not slug:
                continue
            price = svc.get("price")
            qty = svc.get("quantity")
            price_available = price is not None and float(price) > 0
            # Use None for unknown (not yet priced) vs False for confirmed unavailable
            # This prevents greying out services just because pricing hasn't run yet
            if price is None:
                availability = None  # unknown — don't grey out
            else:
                availability = price_available
            stock_map[slug] = {
                "available": availability,
                "price": price,
                "quantity": qty,
                "provider": "textverified",
            }
            if price_available:
                priced_slugs.append(slug)

        # Fetch outcomes only for priced services (typically ~58, not 2351)
        for slug in priced_slugs:
            outcome = await get_purchase_outcome(slug)
            if outcome is not None:
                stock_map[slug]["available"] = outcome

        return stock_map
    except Exception as e:
        logger.warning(f"Failed to build stock map: {e}")
        return {}


async def refresh_stock_cache() -> None:
    """Refresh stock cache from the TV services price cache.

    TV's /api/pub/v2/services does not return quantity — fetch_raw_services_with_quantity
    always returns qty=0 for every service, making everything appear out of stock.
    The only reliable availability signal from TV is: price > 0 = in stock.
    Fires admin alert when a service transitions available → unavailable.
    Notifies stock watchers when a service transitions unavailable → available.
    """
    previous = await cache.get(_STOCK_CACHE_KEY) or {}
    prev_services: dict = previous.get("services", {})

    stock_map = await build_stock_map()

    if stock_map:
        await cache.set(
            _STOCK_CACHE_KEY,
            {
                "services": stock_map,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "total": len(stock_map),
                "available": sum(1 for s in stock_map.values() if s["available"]),
            },
            _STOCK_CACHE_TTL,
        )
        available = sum(1 for s in stock_map.values() if s["available"])
        with_qty = sum(1 for s in stock_map.values() if s.get("quantity") is not None)
        logger.info(
            f"Stock refreshed: {available}/{len(stock_map)} available, {with_qty} with quantity"
        )

        # Detect transitions: available → unavailable → alert admin
        newly_depleted = [
            slug for slug, data in stock_map.items()
            if data.get("available") is False
            and prev_services.get(slug, {}).get("available") is True
        ]
        if newly_depleted:
            try:
                from app.services.alerting_service import alerting_service
                from app.models.stock_watch import StockWatch
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import select, func
                async with AsyncSessionLocal() as db:
                    for slug in newly_depleted:
                        result = await db.execute(
                            select(func.count()).where(
                                StockWatch.service_name == slug,
                                StockWatch.notified_at.is_(None),
                            )
                        )
                        watcher_count = result.scalar() or 0
                        await alerting_service.send_stock_depleted_alert(slug, watcher_count)
            except Exception as e:
                logger.warning(f"Stock depletion alert failed: {e}")

        # Detect transitions: unavailable → available → notify watchers (INV-001)
        newly_available = [
            slug for slug, data in stock_map.items()
            if data.get("available") is True
            and prev_services.get(slug, {}).get("available") is False
        ]
        if newly_available:
            try:
                await _notify_stock_watchers(newly_available, stock_map)
            except Exception as e:
                logger.warning(f"Stock watcher notification failed: {e}")

        # Notify users watching services that just became available
        newly_available = [
            slug for slug, data in stock_map.items()
            if data.get("available") is True
            and prev_services.get(slug, {}).get("available") is not True
        ]
        if newly_available:
            try:
                await _notify_stock_watchers(newly_available, stock_map)
            except Exception as e:
                logger.warning(f"Stock watch notification failed: {e}")


async def _notify_stock_watchers(newly_available: list, stock_map: dict) -> None:
    """Notify users watching services that just came back in stock (INV-001)."""
    try:
        from app.core.database import SessionLocal
        from app.models.stock_watch import StockWatch
        from app.services.notification_service import NotificationService

        db = SessionLocal()
        try:
            for slug in newly_available:
                price = stock_map.get(slug, {}).get("price")
                watches = (
                    db.query(StockWatch)
                    .filter(
                        StockWatch.service_name == slug,
                        StockWatch.notified_at.is_(None),
                    )
                    .all()
                )
                for watch in watches:
                    try:
                        notif_svc = NotificationService(db)
                        notif_svc.create_notification(
                            user_id=watch.user_id,
                            notification_type="stock_available",
                            title=f"\U0001f7e2 {slug.title()} is back in stock",
                            message=(
                                f"{slug.title()} numbers are available again"
                                + (f" at ${price:.2f}" if price else "")
                                + ". Buy now before they sell out."
                            ),
                        )
                        watch.notified_at = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.warning(f"Failed to notify watcher {watch.user_id} for {slug}: {e}")
            db.commit()
            logger.info(f"Notified watchers for {len(newly_available)} newly available services")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"_notify_stock_watchers failed: {e}")


async def get_stock_map() -> dict:
    """Get cached stock map, refreshing if stale."""
    cached = await cache.get(_STOCK_CACHE_KEY)
    if cached:
        return cached
    await refresh_stock_cache()
    return await cache.get(_STOCK_CACHE_KEY) or {}


async def run_stock_monitor() -> None:
    """Background loop — refreshes stock every 90 seconds."""
    logger.info("✅ Service stock monitor started (90s refresh)")
    while True:
        try:
            await refresh_stock_cache()
        except Exception as e:
            logger.warning(f"Stock monitor refresh failed: {e}")
        await asyncio.sleep(
            90
        )  # refresh before 120s TTL expires — keeps cache always warm


async def _notify_stock_watchers(newly_available: list, stock_map: dict) -> None:
    """Notify users watching services that just became available (D-004)."""
    from datetime import datetime, timezone
    from app.core.database import AsyncSessionLocal
    from app.models.stock_watch import StockWatch
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        for slug in newly_available:
            result = await db.execute(
                select(StockWatch).where(
                    StockWatch.service_name == slug,
                    StockWatch.notified_at.is_(None),
                )
            )
            watches = result.scalars().all()
            if not watches:
                continue

            price = stock_map.get(slug, {}).get("price")
            for watch in watches:
                try:
                    from app.services.notification_service import NotificationService
                    notif = NotificationService(db)
                    await notif.create_notification(
                        user_id=watch.user_id,
                        type="stock_available",
                        title=f"{watch.service_name.title()} numbers are back",
                        message=(
                            f"{watch.service_name.title()} numbers are available again"
                            + (f" — ${price:.2f}" if price else "") + ". Buy now."
                        ),
                        data={"service_name": watch.service_name, "price": price},
                    )
                    watch.notified_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.warning(f"Watch notification failed for user {watch.user_id}: {e}")

            await db.commit()
            logger.info(f"Notified {len(watches)} watcher(s) for {slug}")
