"""
Services API Router - SMS Service Management
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.unified_cache import cache
from app.models.user import User
from app.models.verification import Verification
from app.services.stock_monitor import get_stock_map

logger = logging.getLogger(__name__)
from fastapi import HTTPException

router = APIRouter(prefix="/services", tags=["services"])

# Service category map — TV gives no classification, we define it
_CATEGORIES = {
    "social": [
        "whatsapp",
        "telegram",
        "instagram",
        "facebook",
        "twitter",
        "discord",
        "snapchat",
        "tiktok",
        "linkedin",
        "reddit",
        "pinterest",
        "signal",
        "messenger",
        "viber",
        "line",
        "wechat",
        "skype",
        "tumblr",
    ],
    "dating": [
        "tinder",
        "bumble",
        "hinge",
        "match",
        "okcupid",
        "grindr",
        "badoo",
        "pof",
        "zoosk",
    ],
    "finance": [
        "paypal",
        "coinbase",
        "binance",
        "cashapp",
        "venmo",
        "robinhood",
        "revolut",
        "wise",
        "stripe",
        "square",
    ],
    "tech": [
        "google",
        "apple",
        "microsoft",
        "amazon",
        "github",
        "gitlab",
        "dropbox",
        "slack",
        "zoom",
        "teams",
    ],
    "delivery": [
        "uber",
        "doordash",
        "lyft",
        "airbnb",
        "grubhub",
        "postmates",
        "ubereats",
        "instacart",
        "booking",
        "expedia",
    ],
    "streaming": [
        "netflix",
        "spotify",
        "twitch",
        "steam",
        "epicgames",
        "playstation",
        "xbox",
        "nintendo",
        "hulu",
        "disney",
    ],
    "shopping": [
        "walmart",
        "target",
        "ebay",
        "etsy",
        "shopify",
    ],
}


def _get_category(slug: str) -> str:
    s = slug.lower()
    for cat, slugs in _CATEGORIES.items():
        if s in slugs:
            return cat
    return "other"


async def _get_success_rates(db: Session) -> dict:
    """Query our own DB for 7-day success rate and 24h attempt count per service."""
    try:
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        from sqlalchemy import case

        rows = (
            db.query(
                Verification.service_name,
                func.count(Verification.id).label("total"),
                func.sum(case((Verification.status == "completed", 1), else_=0)).label(
                    "completed"
                ),
            )
            .filter(Verification.created_at >= week_ago)
            .group_by(Verification.service_name)
            .all()
        )

        demand_rows = (
            db.query(
                Verification.service_name,
                func.count(Verification.id).label("attempts"),
            )
            .filter(Verification.created_at >= day_ago)
            .group_by(Verification.service_name)
            .all()
        )

        rates = {}
        for row in rows:
            slug = (row.service_name or "").lower()
            total = int(row.total or 0)
            completed = int(row.completed or 0) if row.completed else 0
            rates[slug] = {
                "success_rate": round(completed / total * 100) if total > 0 else None,
                "attempts_7d": total,
            }

        for row in demand_rows:
            slug = (row.service_name or "").lower()
            if slug not in rates:
                rates[slug] = {"success_rate": None, "attempts_7d": 0}
            rates[slug]["attempts_24h"] = int(row.attempts or 0)

        return rates
    except Exception as e:
        logger.warning(f"Failed to compute success rates: {e}")
        return {}


@router.get("/stock")
async def get_services_stock(db: Session = Depends(get_db)):
    """Get real-time stock availability for all services with enriched metadata."""
    try:
        data = await get_stock_map()
        if not data:
            return {"services": {}, "available": 0, "total": 0}

        stats = await _get_success_rates(db)
        services = data.get("services", {})

        enriched = {}
        for slug, info in services.items():
            stat = stats.get(slug, {})
            attempts_24h = stat.get("attempts_24h", 0)
            enriched[slug] = {
                **info,
                "category": _get_category(slug),
                "success_rate": stat.get("success_rate"),
                "attempts_24h": attempts_24h,
                "demand": "high" if attempts_24h >= 10 else "normal",
            }

        return {
            **data,
            "services": enriched,
        }
    except Exception as e:
        logger.error(f"Error in get_services_stock: {e}", exc_info=True)
        return {"services": {}, "available": 0, "total": 0}


@router.get("/status")
async def get_services_status():
    try:
        """Get status of all SMS services (cached 1h)"""
        # Check cache first
        cache_key_str = cache.cache_key("services", "status")
        cached_result = await cache.get(cache_key_str)
        if cached_result:
            return cached_result

        result = {
            "status": "operational",
            "services": {
                "sms_activate": "active",
                "5sim": "active",
                "textverified": "active",
                "getsms": "active",
            },
        }

        # Cache for 1 hour
        await cache.set(cache_key_str, result, ttl=3600)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_services_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/providers")
async def get_providers(current_user: User = Depends(get_current_user)):
    try:
        """Get available SMS providers (cached 1h)"""
        # Check cache first
        cache_key_str = cache.cache_key("services", "providers")
        cached_result = await cache.get(cache_key_str)
        if cached_result:
            return cached_result

        result = {
            "providers": [
                {"name": "SMS - Activate", "status": "active", "countries": 180},
                {"name": "5SIM", "status": "active", "countries": 150},
                {"name": "TextVerified", "status": "active", "countries": 50},
                {"name": "GetSMS", "status": "active", "countries": 100},
            ]
        }

        # Cache for 1 hour
        await cache.set(cache_key_str, result, ttl=3600)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
