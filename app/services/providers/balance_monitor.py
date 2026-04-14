"""Provider balance monitoring.

Runs as a background task inside the SMS polling service loop.
Checks all provider balances every 5 minutes, alerts at $50/$25,
auto-disables at $10.

On Render free tier there is no persistent cron — this piggybacks on
the existing background polling service which is already running.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Thresholds in USD
WARN_THRESHOLD = 50.0
CRITICAL_THRESHOLD = 25.0
DISABLE_THRESHOLD = 10.0

# Check interval
CHECK_INTERVAL_SECONDS = 300  # 5 minutes


async def check_all_balances() -> Dict[str, float]:
    """Fetch balances from all enabled providers."""
    from app.services.providers.provider_router import ProviderRouter

    router = ProviderRouter()
    return await router.get_provider_balances()


async def evaluate_balances(balances: Dict[str, float]) -> None:
    """Evaluate balances and log alerts. Auto-disable providers below threshold."""
    settings = get_settings()

    for provider, balance in balances.items():
        if balance <= DISABLE_THRESHOLD:
            logger.error(
                f"PROVIDER BALANCE CRITICAL: {provider} balance ${balance:.2f} "
                f"is at or below ${DISABLE_THRESHOLD:.2f} — provider disabled"
            )
            _disable_provider(provider, settings)

        elif balance <= CRITICAL_THRESHOLD:
            logger.error(
                f"PROVIDER BALANCE LOW: {provider} balance ${balance:.2f} "
                f"— top up immediately (critical threshold: ${CRITICAL_THRESHOLD:.2f})"
            )
            await _send_alert(provider, balance, "critical")

        elif balance <= WARN_THRESHOLD:
            logger.warning(
                f"PROVIDER BALANCE WARNING: {provider} balance ${balance:.2f} "
                f"— consider topping up (warning threshold: ${WARN_THRESHOLD:.2f})"
            )
            await _send_alert(provider, balance, "warning")

        else:
            logger.debug(f"Provider {provider} balance OK: ${balance:.2f}")


def _disable_provider(provider: str, settings) -> None:
    """Disable a provider at runtime when balance is critically low.

    Sets the enabled flag in settings so the router stops routing to it.
    This is a runtime-only change — does not modify env vars.
    """
    if provider == "telnyx":
        settings.telnyx_enabled = False
        logger.error("Telnyx auto-disabled due to low balance")
    elif provider == "5sim":
        settings.fivesim_enabled = False
        logger.error("5sim auto-disabled due to low balance")
    # TextVerified is never auto-disabled — it's the primary provider


async def _send_alert(provider: str, balance: float, level: str) -> None:
    """Send balance alert via notification service."""
    try:
        from app.core.database import SessionLocal
        from app.services.notification_service import NotificationService

        db = SessionLocal()
        try:
            notif_service = NotificationService(db)
            title = f"Provider Balance {level.title()}: {provider}"
            message = (
                f"{provider} balance is ${balance:.2f}. "
                f"{'Top up immediately.' if level == 'critical' else 'Consider topping up.'}"
            )
            # Notify admin (user_id="admin" is handled by NotificationService)
            notif_service.create_admin_notification(
                notification_type=f"provider_balance_{level}",
                title=title,
                message=message,
            )
        finally:
            db.close()
    except Exception as e:
        # Alert failure must never crash the monitor
        logger.warning(f"Failed to send balance alert for {provider}: {e}")


async def run_balance_monitor() -> None:
    """Background loop — checks balances every 5 minutes indefinitely."""
    logger.info("Provider balance monitor started")

    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

            balances = await check_all_balances()
            if balances:
                await evaluate_balances(balances)
                logger.info(
                    f"Balance check complete at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}: "
                    + ", ".join(f"{p}=${b:.2f}" for p, b in balances.items())
                )

        except asyncio.CancelledError:
            logger.info("Provider balance monitor stopped")
            break
        except Exception as e:
            # Never crash the monitor loop
            logger.error(f"Balance monitor error (will retry in 5 min): {e}")
