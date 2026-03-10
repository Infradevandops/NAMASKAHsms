"""Enhanced Redis cache with invalidation patterns and monitoring."""

import json
import time
from typing import Any, Dict, List, Optional

import redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Enhanced cache manager with invalidation patterns and monitoring."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0

        # Cache TTL configurations
        self.ttl_config = {
            "user_tier": 3600,  # 1 hour
            "service_pricing": 86400,  # 24 hours
            "area_codes": 7200,  # 2 hours
            "carriers": 86400,  # 24 hours
            "user_balance": 300,  # 5 minutes
            "verification_status": 60,  # 1 minute
            "default": 1800,  # 30 minutes
        }

    @property
    def client(self):
        """Get Redis client with connection validation."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                self._client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.error_count += 1
                raise
        return self._client

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with metrics tracking."""
        try:
            value = self.client.get(key)
            if value is not None:
                self.hit_count += 1
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                self.miss_count += 1
                return default
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.error_count += 1
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: str = "default",
    ) -> bool:
        """Set value in cache with TTL configuration."""
        try:
            if ttl is None:
                ttl = self.ttl_config.get(cache_type, self.ttl_config["default"])

            serialized_value = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            result = self.client.setex(key, ttl, serialized_value)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.error_count += 1
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.error_count += 1
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
            self.error_count += 1
            return 0

    def warm_cache(self, cache_entries: Dict[str, Dict]) -> int:
        """Warm cache with multiple entries."""
        warmed = 0
        try:
            pipe = self.client.pipeline()
            for key, config in cache_entries.items():
                value = config["value"]
                ttl = config.get("ttl", self.ttl_config["default"])
                cache_type = config.get("type", "default")

                serialized_value = (
                    json.dumps(value) if not isinstance(value, str) else value
                )
                pipe.setex(key, ttl, serialized_value)
                warmed += 1

            pipe.execute()
            logger.info(f"Cache warmed with {warmed} entries")
            return warmed
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            self.error_count += 1
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        try:
            info = self.client.info("memory")
            redis_stats = {
                "memory_used": info.get("used_memory_human", "unknown"),
                "memory_peak": info.get("used_memory_peak_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            redis_stats = {"error": str(e)}

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "error_count": self.error_count,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "redis_stats": redis_stats,
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        try:
            start_time = time.time()
            self.client.ping()
            ping_time = round((time.time() - start_time) * 1000, 2)

            # Test set/get
            test_key = "health_check_test"
            test_value = "test_value"
            self.client.setex(test_key, 10, test_value)
            retrieved_value = self.client.get(test_key)
            self.client.delete(test_key)

            if retrieved_value != test_value:
                return {"status": "degraded", "error": "Set/get test failed"}

            return {"status": "healthy", "ping_time_ms": ping_time, "test_passed": True}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "test_passed": False}


# Global cache manager instance
cache_manager = CacheManager()


def get_redis():
    """Get Redis client (legacy compatibility)."""
    return cache_manager.client


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return cache_manager
