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


async def build_stock_map() -> Dict[str, dict]:
    """Build availability map from cached TextVerified services list."""
    try:
        services = await cache.get(_TV_SERVICES_KEY)
        if not services:
            return {}

        stock_map = {}
        for svc in services:
            # Use id field directly — matches what ServiceStore uses as item.value
            slug = (svc.get("id") or svc.get("name") or "").lower().strip()
            if not slug:
                continue
            price = svc.get("price")
            stock_map[slug] = {
                "available": price is not None and float(price) > 0,
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
