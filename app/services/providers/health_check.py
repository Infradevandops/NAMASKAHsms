"""Provider health checks — run on startup to validate all configured providers."""

from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_textverified_health() -> dict:
    """Validate TextVerified is configured and reachable.

    TextVerified is the primary provider. If this fails the app logs a hard
    error but does NOT refuse to start — Render would mark the deploy failed
    and roll back, which is worse than starting degraded.
    """
    from app.services.textverified_service import TextVerifiedService

    svc = TextVerifiedService()

    if not svc.enabled:
        logger.error(
            "TextVerified DISABLED — TEXTVERIFIED_API_KEY or TEXTVERIFIED_EMAIL not set. "
            "SMS verification will not work."
        )
        return {"provider": "textverified", "status": "disabled", "balance": None}

    try:
        balance_data = await svc.get_balance()
        balance = balance_data.get("balance", 0.0)
        logger.info(f"TextVerified healthy — balance: ${balance:.2f}")
        return {"provider": "textverified", "status": "ok", "balance": balance}
    except Exception as e:
        logger.error(f"TextVerified health check failed: {e}")
        return {"provider": "textverified", "status": "error", "balance": None, "error": str(e)}


async def check_telnyx_health() -> dict:
    """Validate Telnyx is configured and reachable (warn only, non-critical)."""
    from app.services.providers.telnyx_adapter import TelnyxAdapter

    adapter = TelnyxAdapter()

    if not adapter.enabled:
        logger.info("Telnyx not configured — TELNYX_API_KEY not set (optional provider)")
        return {"provider": "telnyx", "status": "disabled", "balance": None}

    try:
        balance = await adapter.get_balance()
        logger.info(f"Telnyx healthy — balance: ${balance:.2f}")
        return {"provider": "telnyx", "status": "ok", "balance": balance}
    except Exception as e:
        logger.warning(f"Telnyx health check failed (non-critical): {e}")
        return {"provider": "telnyx", "status": "error", "balance": None, "error": str(e)}


async def check_fivesim_health() -> dict:
    """Validate 5sim is configured and reachable (warn only, non-critical)."""
    from app.services.providers.fivesim_adapter import FiveSimAdapter

    adapter = FiveSimAdapter()

    if not adapter.enabled:
        logger.info("5sim not configured — FIVESIM_API_KEY not set (optional provider)")
        return {"provider": "5sim", "status": "disabled", "balance": None}

    try:
        balance = await adapter.get_balance()
        logger.info(f"5sim healthy — balance: ${balance:.2f}")
        return {"provider": "5sim", "status": "ok", "balance": balance}
    except Exception as e:
        logger.warning(f"5sim health check failed (non-critical): {e}")
        return {"provider": "5sim", "status": "error", "balance": None, "error": str(e)}


async def run_provider_health_checks() -> dict:
    """Run all provider health checks on startup.

    TextVerified failure -> logged as ERROR (primary provider down)
    Telnyx/5sim failure  -> logged as WARNING (optional providers)

    Returns dict of results for logging/monitoring.
    """
    import asyncio

    tv, telnyx, fivesim = await asyncio.gather(
        check_textverified_health(),
        check_telnyx_health(),
        check_fivesim_health(),
    )

    results = {
        "textverified": tv,
        "telnyx": telnyx,
        "5sim": fivesim,
    }

    enabled = [p for p, r in results.items() if r["status"] == "ok"]
    disabled = [p for p, r in results.items() if r["status"] == "disabled"]
    errors = [p for p, r in results.items() if r["status"] == "error"]

    logger.info(
        f"Provider health check complete — "
        f"enabled: {enabled}, disabled: {disabled}, errors: {errors}"
    )

    return results
