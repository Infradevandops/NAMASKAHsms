"""Webhook service for event delivery."""
import hmac
import hashlib
import json
from typing import Dict, Any
import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookService:
    """Manages webhook registration and delivery."""

    def __init__(self):
        self.webhooks = {}
        self.timeout = 10

    async def register(self, user_id: str, url: str, events: list) -> str:
        """Register webhook."""
        webhook_id = f"wh_{user_id}_{len(self.webhooks)}"
        self.webhooks[webhook_id] = {
            "url": url,
            "events": events,
            "active": True,
            "retries": 0
        }
        logger.info(f"Webhook registered: {webhook_id}")
        return webhook_id

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign webhook payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def deliver(self, webhook_id: str, event: str,
                      data: Dict[str, Any], secret: str):
        """Deliver webhook event."""
        if webhook_id not in self.webhooks:
            return

        webhook = self.webhooks[webhook_id]
        if event not in webhook["events"] or not webhook["active"]:
            return

        payload = json.dumps({"event": event, "data": data})
        signature = self._sign_payload(payload, secret)

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook["url"],
                    content=payload,
                    headers={
                        "X - Webhook-Signature": signature,
                        "Content - Type": "application/json"
                    },
                    timeout=self.timeout
                )
                webhook["retries"] = 0
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            webhook["retries"] += 1
            if webhook["retries"] > 3:
                webhook["active"] = False

    async def get_webhooks(self, user_id: str) -> list:
        """Get user webhooks."""
        return [
            {"id": wh_id, **wh}
            for wh_id, wh in self.webhooks.items()
            if user_id in wh_id
        ]


webhook_service = WebhookService()
