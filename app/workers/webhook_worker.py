"""Background worker for webhook processing."""


import asyncio
from redis import Redis
from app.core.config import get_settings
from app.services.webhook_queue import WebhookQueue

async def run_webhook_worker():
    """Run webhook worker continuously."""
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    queue = WebhookQueue(redis)

while True:
try:
            await queue.process_batch(batch_size=10)
except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_webhook_worker())