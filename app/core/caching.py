"""Caching layer implementation for task 12.2."""
import json
from typing import Any, Optional, Dict
import redis.asyncio as redis
from app.core.config import settings


class CacheManager:
    """Redis-based caching manager."""
    
    def __init__(self):
        self.redis_client = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis."""
        if not self._connected:
            self.redis_client = redis.from_url(
                settings.redis_url or "redis://localhost:6379",
                decode_responses=True,
                max_connections=20
            )
            self._connected = True
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            return json.loads(value) if value else None
        except (redis.RedisError, json.JSONDecodeError, ValueError):
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL."""
        if not self._connected:
            await self.connect()
        
        try:
            await self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except (redis.RedisError, json.JSONEncodeError, ValueError):
            pass
    
    async def delete(self, key: str):
        """Delete key from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
        except (redis.RedisError, ValueError):
            pass
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern."""
        if not self._connected:
            await self.connect()
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except (redis.RedisError, ValueError):
            pass


# Global cache instance
cache = CacheManager()


def cache_key(prefix: str, *args) -> str:
    """Generate cache key."""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"


async def cached_services_list():
    """Cache services list."""
    key = cache_key("services", "list")
    cached = await cache.get(key)
    
    if cached:
        return cached
    
    # Fetch from external API (mock)
    services = [
        {"name": "telegram", "price": 0.5},
        {"name": "whatsapp", "price": 0.7}
    ]
    
    await cache.set(key, services, ttl=3600)  # 1 hour
    return services


async def cached_user_stats(user_id: str):
    """Cache user statistics."""
    key = cache_key("user_stats", user_id)
    cached = await cache.get(key)
    
    if cached:
        return cached
    
    # Calculate stats (mock)
    stats = {
        "total_verifications": 10,
        "successful_verifications": 8,
        "total_spent": 15.0
    }
    
    await cache.set(key, stats, ttl=900)  # 15 minutes
    return stats


async def invalidate_user_cache(user_id: str):
    """Invalidate all user-related cache."""
    await cache.invalidate_pattern(f"user_stats:{user_id}*")
    await cache.invalidate_pattern(f"user_verifications:{user_id}*")