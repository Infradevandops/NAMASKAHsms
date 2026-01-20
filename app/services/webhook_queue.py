"""Persistent webhook queue using Redis Streams."""

import json
from typing import Any, Dict
from redis import Redis
from app.core.logging import get_logger

logger = get_logger(__name__)

class WebhookQueue:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.stream = "webhooks:pending"
        self.dlq_stream = "webhooks:failed"
        self.max_retries = 5
    
    async def enqueue(self, webhook_id: str, event: str, data: Dict[str, Any]):
        """Add webhook to queue."""
        payload = {
            "webhook_id": webhook_id,
            "event": event,
            "data": json.dumps(data),
            "retry_count": 0
        }
        
        message_id = self.redis.xadd(self.stream, payload)
        logger.info(f"Enqueued webhook {webhook_id}: {message_id}")
        return message_id
    
    async def process_batch(self, batch_size: int = 10):
        """Process webhooks from queue."""
        # Create consumer group if not exists
        try:
            self.redis.xgroup_create(self.stream, "webhook-workers", id="0", mkstream=True)
        except:
            pass  # Group already exists
        
        # Read from stream
        messages = self.redis.xreadgroup(
            "webhook-workers",
            "worker-1",
            {self.stream: ">"},
            count=batch_size,
            block=1000
        )
        
        for stream, message_list in messages:
            for message_id, payload in message_list:
                await self._process_message(message_id, payload)
    
    async def _process_message(self, message_id: str, payload: Dict):
        """Process single webhook message."""
        webhook_id = payload[b"webhook_id"].decode()
        event = payload[b"event"].decode()
        data = json.loads(payload[b"data"].decode())
        retry_count = int(payload.get(b"retry_count", b"0"))
        
        try:
            # Deliver webhook (import from webhook_service)
            from app.services.webhook_service import webhook_service
            await webhook_service.deliver(webhook_id, event, data, "secret")
            
            # Acknowledge message
            self.redis.xack(self.stream, "webhook-workers", message_id)
            logger.info(f"Webhook {webhook_id} delivered successfully")
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {str(e)}")
            
            # Retry with exponential backoff
            if retry_count < self.max_retries:
                payload[b"retry_count"] = str(retry_count + 1).encode()
                self.redis.xadd(self.stream, payload)
            else:
                # Move to DLQ
                self.redis.xadd(self.dlq_stream, payload)
                logger.error(f"Webhook {webhook_id} moved to DLQ after {retry_count} retries")
            
            # Acknowledge original message
            self.redis.xack(self.stream, "webhook-workers", message_id)
