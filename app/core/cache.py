"""Redis cache connection utilities."""


import redis
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_redis():
    """Get a synchronized Redis client."""
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        # Test connection
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Return a mock or raise depending on policy
        # For now, we'll let it raise so the caller knows
        raise