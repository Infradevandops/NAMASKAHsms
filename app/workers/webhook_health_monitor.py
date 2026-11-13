"""TV webhook health monitor.

TV auto-disables our webhook endpoint after repeated delivery failures
(e.g. during deploys when the server is briefly unreachable).

This worker checks every 30 minutes and re-enables the webhook if disabled.
"""

import asyncio
import os

from app.core.logging import get_logger

logger = get_logger(__name__)

_TV_API_BASE = "https://app.textverified.com/api/pub/v2"


async def run_webhook_health_monitor():
    """Background loop — checks TV webhook status every 30 minutes."""
    while True:
        try:
            await _check_and_heal()
        except Exception as e:
            logger.error(f"Webhook health monitor error: {e}")
        await asyncio.sleep(1800)  # 30 min


async def _check_and_heal():
    import asyncio as _asyncio
    import requests

    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    if not api_key:
        return

    webhook_url = os.getenv("VRENUM_WEBHOOK_URL") or os.getenv("APP_BASE_URL", "")
    if not webhook_url:
        return
    endpoint = f"{webhook_url}/api/verification/webhook/tv"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # Fetch current webhook config
        resp = await _asyncio.to_thread(
            requests.get, f"{_TV_API_BASE}/webhooks", headers=headers, timeout=10
        )
        if resp.status_code != 200:
            logger.warning(f"Webhook health: TV webhooks fetch returned {resp.status_code}")
            return

        data = resp.json()
        webhooks = data.get("data", []) if isinstance(data, dict) else data

        # Find our webhook
        our_hook = next(
            (w for w in webhooks if endpoint in str(w.get("url", ""))), None
        )

        if our_hook is None:
            # Register it
            logger.warning("Webhook health: our webhook not found in TV — registering")
            await _asyncio.to_thread(
                requests.post,
                f"{_TV_API_BASE}/webhooks",
                headers=headers,
                json={"url": endpoint, "enabled": True},
                timeout=10,
            )
            logger.info("Webhook health: webhook registered")
            return

        if not our_hook.get("enabled", True):
            # Re-enable it
            hook_id = our_hook.get("id")
            logger.warning(f"Webhook health: TV webhook {hook_id} is disabled — re-enabling")
            await _asyncio.to_thread(
                requests.patch,
                f"{_TV_API_BASE}/webhooks/{hook_id}",
                headers=headers,
                json={"enabled": True},
                timeout=10,
            )
            logger.info(f"Webhook health: webhook {hook_id} re-enabled")

    except Exception as e:
        logger.warning(f"Webhook health check failed (non-critical): {e}")
