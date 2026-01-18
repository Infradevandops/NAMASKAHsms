"""Unified caching system with Redis and in - memory fallback."""

import json
import time
import functools
from typing import Any, Optional, Callable, Dict
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class InMemoryCache:
    """Simple in - memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        if key in self._expiry and time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None

        return self._cache[key]

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL."""
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl

    async def delete(self, key: str):
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)

    async def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._expiry.clear()

    async def keys(self, pattern: str = "*"):
        """Get keys matching pattern."""
        import fnmatch

        return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]


class UnifiedCacheManager:
    """Unified cache manager with Redis primary and in - memory fallback."""

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.memory_cache = InMemoryCache()
        self._connected = False

        # Default TTL values for different data types
        self.ttl_defaults = {
            "countries": 86400,  # 24h
            "services": 3600,  # 1h
            "verification": 300,  # 5m
            "user": 1800,  # 30m
            "provider": 600,  # 10m
            "default": 3600,  # 1h
        }

    async def connect(self):
        """Connect to Redis with fallback to in - memory."""
        if self._connected:
            return

        try:
            redis_url = getattr(settings, "redis_url", None) or "redis://localhost:6379"
            self.redis_client = aioredis.from_url(
                redis_url, decode_responses=True, max_connections=20, retry_on_timeout=True
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in - memory cache: {e}")
            self.redis_client = None
            self._connected = True

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
        self._connected = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis first, then memory)."""
        if not self._connected:
            await self.connect()

        # Try Redis first
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # Fallback to memory cache
        return await self.memory_cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache (both Redis and memory)."""
        if not self._connected:
            await self.connect()

        ttl = ttl or self.ttl_defaults["default"]

        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # Always set in memory cache as backup
        await self.memory_cache.set(key, value, ttl)

    async def delete(self, key: str):
        """Delete key from both caches."""
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")

        await self.memory_cache.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        # Redis pattern invalidation
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis cache keys")
            except Exception as e:
                logger.warning(f"Redis pattern invalidation error: {e}")

        # Memory cache pattern invalidation
        memory_keys = await self.memory_cache.keys(pattern)
        for key in memory_keys:
            await self.memory_cache.delete(key)

        if memory_keys:
            logger.info(f"Invalidated {len(memory_keys)} memory cache keys")

    async def clear(self):
        """Clear all caches."""
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")

        await self.memory_cache.clear()
        logger.info("All caches cleared")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "redis_connected": self.redis_client is not None,
            "memory_keys": len(self.memory_cache._cache),
        }

        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update(
                    {
                        "redis_used_memory": info.get("used_memory_human"),
                        "redis_connected_clients": info.get("connected_clients"),
                        "redis_total_commands": info.get("total_commands_processed"),
                    }
                )
            except Exception as e:
                logger.warning(f"Redis stats error: {e}")

        return stats

    def cache_key(self, prefix: str, *args) -> str:
        """Generate standardized cache key."""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"

    def cached(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """Decorator for caching function results."""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache_key(key_prefix or func.__name__, *args, **kwargs)

                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Store in cache
                await self.set(cache_key, result, ttl)
                logger.debug(f"Cache set: {cache_key}")
                return result

            return wrapper

        return decorator

    def invalidate_on_change(self, pattern: str):
        """Decorator to invalidate cache after function execution."""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                await self.invalidate_pattern(pattern)
                logger.info(f"Invalidated cache pattern: {pattern}")
                return result

            return wrapper

        return decorator


# Global unified cache instance
cache = UnifiedCacheManager()

# Convenience functions for common caching patterns


async def cache_countries(data: Any, ttl: Optional[int] = None):
    """Cache countries data."""
    await cache.set("countries:all", data, ttl or cache.ttl_defaults["countries"])


async def cache_services(country: str, data: Any, ttl: Optional[int] = None):
    """Cache services data for a country."""
    key = cache.cache_key("services", country)
    await cache.set(key, data, ttl or cache.ttl_defaults["services"])


async def cache_user_data(user_id: str, data: Any, ttl: Optional[int] = None):
    """Cache user data."""
    key = cache.cache_key("user", user_id)
    await cache.set(key, data, ttl or cache.ttl_defaults["user"])


async def invalidate_user_cache(user_id: str):
    """Invalidate all user - related cache."""
    await cache.invalidate_pattern(f"user:{user_id}*")
    await cache.invalidate_pattern(f"verification:{user_id}*")


async def cache_verification(verification_id: str, data: Any, ttl: Optional[int] = None):
    """Cache verification data."""
    key = cache.cache_key("verification", verification_id)
    await cache.set(key, data, ttl or cache.ttl_defaults["verification"])


async def cache_provider_data(provider: str, data_type: str, data: Any, ttl: Optional[int] = None):
    """Cache provider - specific data."""
    key = cache.cache_key("provider", provider, data_type)
    await cache.set(key, data, ttl or cache.ttl_defaults["provider"])
