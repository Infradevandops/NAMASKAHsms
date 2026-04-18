"""Provider health and liquidity audit service (V6.0 Mastery)."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.system import ActivityLog
from app.services.providers.provider_router import ProviderRouter

logger = get_logger(__name__)

# Institutional Mastery: Critical threshold for provider liquidity
# Below this, the platform risks total service disruption for high-volume users.
LIQUIDITY_THRESHOLD = 10.00


async def perform_liquidity_audit(db_session: Session = None):
    """Perform a system-wide audit of provider liquidity and health.

    Scans all enabled providers, checks real-time balances, and emits
    ActivityLog alarms if thresholds are breached.
    """
    db = db_session or SessionLocal()
    router = ProviderRouter()

    try:
        enabled_providers = router.get_enabled_providers()
        balances = await router.get_provider_balances()

        for name in enabled_providers:
            balance = balances.get(name, 0.0)

            if balance < LIQUIDITY_THRESHOLD:
                logger.warning(
                    f"⚠️ LIQUIDITY ALARM: Provider '{name}' balance is low (${balance:.2f})"
                )

                # Check if we already logged a critical alarm in the last 12 hours to avoid spam
                # (Implementation detail: for now we just log it)

                # Create ActivityLog entry for Institutional Admin Panel
                log = ActivityLog(
                    user_id="SYSTEM",
                    action="LIQUIDITY_ALARM",
                    element=name,
                    status="CRITICAL",
                    details=f"Provider {name} liquidity below ${LIQUIDITY_THRESHOLD:.2f}.",
                    error_message=f"Current Balance: ${balance:.2f}. Immediate top-up required for V6.0 stability.",
                )
                db.add(log)
                db.commit()

        logger.info(
            f"✓ Liquidity audit complete for {len(enabled_providers)} providers."
        )

    except Exception as e:
        logger.error(f"Provider health audit failed: {e}")
    finally:
        if not db_session:
            db.close()


async def start_health_audit_loop():
    """Background loop for health and liquidity audits.

    Intended to be called by the main application lifecycle manager.
    """
    logger.info("Initializing Institutional Health Audit Loop (Every 4 Hours)...")
    while True:
        await perform_liquidity_audit()
        # Sleep for 4 hours
        await asyncio.sleep(4 * 3600)
