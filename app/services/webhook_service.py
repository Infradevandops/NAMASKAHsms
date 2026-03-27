"""Webhook service for event delivery."""

import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, Optional

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookService:
    """Manages webhook registration and delivery."""

    def __init__(self, db=None):
        self.db = db
        self.webhooks = {}
        self.timeout = 10

    # --- Sync CRUD methods used by API and tests ---

    def create_webhook(self, user_id: str, url: str, events: list) -> dict:
        if not url.startswith("http://") and not url.startswith("https://"):
            return {"success": False, "error": "Invalid URL"}
        secret = uuid.uuid4().hex
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        self.webhooks[webhook_id] = {
            "user_id": user_id,
            "url": url,
            "events": events,
            "secret": secret,
            "active": True,
            "retries": 0,
        }
        return {"success": True, "webhook_id": webhook_id, "secret": secret}

    def list_webhooks(self, user_id: str) -> list:
        return [
            {"id": wh_id, **{k: v for k, v in wh.items() if k != "secret"}}
            for wh_id, wh in self.webhooks.items()
            if wh.get("user_id") == user_id
        ]

    def delete_webhook(self, webhook_id: str, user_id: str) -> dict:
        wh = self.webhooks.get(webhook_id)
        if not wh or wh.get("user_id") != user_id:
            return {"success": False, "error": "Not found"}
        del self.webhooks[webhook_id]
        return {"success": True}

    def generate_signature(self, payload: str, secret: str) -> str:
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        expected = self.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    async def trigger_webhook(self, url: str, event: str, data: Dict[str, Any]) -> dict:
        payload = json.dumps({"event": event, "data": data})
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    url,
                    content=payload,
                    headers={"Content-Type": "application/json"},
                )
                return {"success": resp.status_code < 400}
        except Exception as e:
            logger.error(f"Webhook trigger failed: {e}")
            return {"success": False, "error": str(e)}

    async def register(self, user_id: str, url: str, events: list) -> str:
        """Register webhook."""
        webhook_id = f"wh_{user_id}_{len(self.webhooks)}"
        self.webhooks[webhook_id] = {
            "url": url,
            "events": events,
            "active": True,
            "retries": 0,
        }
        logger.info(f"Webhook registered: {webhook_id}")
        return webhook_id

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign webhook payload."""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    async def deliver(
        self, webhook_id: str, event: str, data: Dict[str, Any], secret: str
    ):
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
                        "Content - Type": "application/json",
                    },
                    timeout=self.timeout,
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
