"""Service stock availability monitor.

Uses the existing TextVerified services cache (tv:services_list) to derive
real-time stock status. price=null means out of stock on TextVerified.
Stores a lightweight availability map in Redis for fast frontend reads.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict

from app.core.logging import get_logger
from app.core.unified_cache import cache

logger = get_logger(__name__)

_STOCK_CACHE_KEY = "services:stock"
_STOCK_CACHE_TTL = 900  # 15 minutes
_TV_SERVICES_KEY = "tv:services_list"
_OUTCOME_TTL = 600  # 10 min — short enough to recover when TV restocks


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


async def get_purchase_outcome(service_slug: str) -> bool | None:
    """Return last known purchase outcome, or None if no recent data."""
    try:
        data = await cache.get(f"services:outcome:{service_slug.lower()}")
        return data["available"] if data else None
    except Exception:
        return None


async def build_stock_map() -> Dict[str, dict]:
    """Build availability map from cached TextVerified services list,
    corrected by real purchase outcomes."""
    try:
        services = await cache.get(_TV_SERVICES_KEY)
        if not services:
            return {}

        stock_map = {}
        for svc in services:
            slug = (svc.get("id") or svc.get("name") or "").lower().strip()
            if not slug:
                continue
            price = svc.get("price")
            # Price > 0 means TV lists it — but check real outcome first
            outcome = await get_purchase_outcome(slug)
            if outcome is not None:
                available = outcome  # Real purchase result overrides price signal
            else:
                available = price is not None and float(price) > 0
            stock_map[slug] = {
                "available": available,
                "price": price,
                "provider": "textverified",
            }

        return stock_map
    except Exception as e:
        logger.warning(f"Failed to build stock map: {e}")
        return {}


async def refresh_stock_cache() -> None:
    """Refresh the stock availability cache from provider data."""
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
        logger.info(
            f"Stock cache refreshed: {available}/{len(stock_map)} services available"
        )


async def get_stock_map() -> dict:
    """Get cached stock map, refreshing if stale."""
    cached = await cache.get(_STOCK_CACHE_KEY)
    if cached:
        return cached
    await refresh_stock_cache()
    return await cache.get(_STOCK_CACHE_KEY) or {}


async def run_stock_monitor() -> None:
    """Background loop — refreshes stock every 15 minutes."""
    logger.info("✅ Service stock monitor started (15-min refresh)")
    while True:
        try:
            await refresh_stock_cache()
        except Exception as e:
            logger.warning(f"Stock monitor refresh failed: {e}")
        await asyncio.sleep(_STOCK_CACHE_TTL)
