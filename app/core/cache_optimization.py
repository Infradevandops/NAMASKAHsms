"""Cache optimization for tier identification system.

Implements:
- Adaptive TTL based on hit rates
- Cache warming strategies
- Cache invalidation policies
- Memory management
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """Optimizes cache performance with adaptive strategies."""

    def __init__(self, redis_client=None):
        """Initialize cache optimizer.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0,
        }
        self.ttl_config = {
            "tier": 3600,  # 1 hour
            "features": 7200,  # 2 hours
            "user": 1800,  # 30 minutes
            "verification": 600,  # 10 minutes
        }
        self.max_cache_size = 1073741824  # 1GB

    def get_optimal_ttl(self, cache_type: str, hit_rate: float = None) -> int:
        """Calculate optimal TTL based on hit rate.

        Args:
            cache_type: Type of cache (tier, features, user, verification)
            hit_rate: Current hit rate (0-1)

        Returns:
            Optimal TTL in seconds
        """
        base_ttl = self.ttl_config.get(cache_type, 3600)

        if hit_rate is None:
            return base_ttl

        # Adjust TTL based on hit rate
        if hit_rate > 0.95:
            # High hit rate - increase TTL
            return int(base_ttl * 1.5)
        elif hit_rate > 0.85:
            # Good hit rate - keep as is
            return base_ttl
        elif hit_rate > 0.70:
            # Moderate hit rate - decrease TTL slightly
            return int(base_ttl * 0.8)
        else:
            # Low hit rate - decrease TTL significantly
            return int(base_ttl * 0.5)

    def warm_cache(self, cache_type: str, data: Dict[str, Any]) -> bool:
        """Warm cache with frequently accessed data.

        Args:
            cache_type: Type of cache to warm
            data: Data to cache

        Returns:
            True if successful
        """
        try:
            if not self.redis:
                logger.warning("Redis not available for cache warming")
                return False

            ttl = self.ttl_config.get(cache_type, 3600)
            key = f"cache:warm:{cache_type}"

            # Serialize data
            serialized = json.dumps(data)

            # Set in cache with TTL
            self.redis.setex(key, ttl, serialized)

            logger.info(f"Cache warmed: {cache_type} ({len(serialized)} bytes)")
            return True

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return False

    def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "tier:*")

        Returns:
            Number of keys deleted
        """
        try:
            if not self.redis:
                return 0

            # Find keys matching pattern
            keys = self.redis.keys(pattern)

            if not keys:
                return 0

            # Delete keys
            deleted = self.redis.delete(*keys)

            logger.info(f"Cache invalidated: {pattern} ({deleted} keys)")
            self.stats["evictions"] += deleted

            return deleted

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "total_size": self.stats["total_size"],
            "ttl_config": self.ttl_config,
        }

    def optimize_memory(self) -> bool:
        """Optimize cache memory usage.

        Returns:
            True if optimization successful
        """
        try:
            if not self.redis:
                return False

            # Get current memory usage
            info = self.redis.info("memory")
            used_memory = info.get("used_memory", 0)

            if used_memory > self.max_cache_size:
                logger.warning(
                    f"Cache size ({used_memory} bytes) exceeds limit "
                    f"({self.max_cache_size} bytes)"
                )

                # Evict least recently used keys
                self.redis.execute_command("MEMORY", "PURGE")

                logger.info("Cache memory optimized")
                return True

            return False

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False

    def track_hit(self, hit: bool):
        """Track cache hit or miss.

        Args:
            hit: True if cache hit, False if miss
        """
        if hit:
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1

    def update_cache_size(self, size: int):
        """Update total cache size.

        Args:
            size: Cache size in bytes
        """
        self.stats["total_size"] = size


class CacheWarmer:
    """Warms cache with frequently accessed data."""

    def __init__(self, db_session=None, redis_client=None):
        """Initialize cache warmer.

        Args:
            db_session: Database session
            redis_client: Redis client
        """
        self.db = db_session
        self.redis = redis_client
        self.optimizer = CacheOptimizer(redis_client)

    def warm_tier_cache(self) -> bool:
        """Warm tier configuration cache.

        Returns:
            True if successful
        """
        try:
            if not self.db:
                return False

            # Get all tier configurations
            from app.models.subscription_tier import SubscriptionTier

            tiers = self.db.query(SubscriptionTier).all()

            tier_data = {
                tier.name: {
                    "name": tier.name,
                    "price": str(tier.price),
                    "features": tier.features,
                    "limits": tier.limits,
                }
                for tier in tiers
            }

            return self.optimizer.warm_cache("tier_config", tier_data)

        except Exception as e:
            logger.error(f"Tier cache warming failed: {e}")
            return False

    def warm_feature_cache(self) -> bool:
        """Warm feature access cache.

        Returns:
            True if successful
        """
        try:
            if not self.db:
                return False

            # Get all feature definitions
            feature_data = {
                "api_access": {"tier": "pro", "cost": 0},
                "area_codes": {"tier": "payg", "cost": 0.25},
                "isp_filtering": {"tier": "payg", "cost": 0.50},
                "webhooks": {"tier": "pro", "cost": 0},
                "priority_routing": {"tier": "custom", "cost": 0},
                "custom_branding": {"tier": "custom", "cost": 0},
            }

            return self.optimizer.warm_cache("features", feature_data)

        except Exception as e:
            logger.error(f"Feature cache warming failed: {e}")
            return False

    def warm_all_caches(self) -> Dict[str, bool]:
        """Warm all caches.

        Returns:
            Results for each cache type
        """
        results = {
            "tier_config": self.warm_tier_cache(),
            "features": self.warm_feature_cache(),
        }

        logger.info(f"Cache warming complete: {results}")
        return results


class CacheInvalidationPolicy:
    """Manages cache invalidation policies."""

    def __init__(self, redis_client=None):
        """Initialize invalidation policy.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client
        self.policies = {
            "tier_change": ["tier:*", "user:*"],
            "feature_change": ["features:*"],
            "config_change": ["config:*"],
        }

    def on_tier_change(self, user_id: str) -> int:
        """Invalidate cache on tier change.

        Args:
            user_id: User ID

        Returns:
            Number of keys invalidated
        """
        try:
            if not self.redis:
                return 0

            # Invalidate user-specific caches
            patterns = [f"tier:{user_id}:*", f"user:{user_id}:*"]
            total_deleted = 0

            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    total_deleted += self.redis.delete(*keys)

            logger.info(
                f"Cache invalidated on tier change: {user_id} ({total_deleted} keys)"
            )
            return total_deleted

        except Exception as e:
            logger.error(f"Tier change invalidation failed: {e}")
            return 0

    def on_feature_change(self) -> int:
        """Invalidate cache on feature change.

        Returns:
            Number of keys invalidated
        """
        try:
            if not self.redis:
                return 0

            # Invalidate feature caches
            keys = self.redis.keys("features:*")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cache invalidated on feature change ({deleted} keys)")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Feature change invalidation failed: {e}")
            return 0

    def on_config_change(self) -> int:
        """Invalidate cache on config change.

        Returns:
            Number of keys invalidated
        """
        try:
            if not self.redis:
                return 0

            # Invalidate config caches
            keys = self.redis.keys("config:*")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cache invalidated on config change ({deleted} keys)")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Config change invalidation failed: {e}")
            return 0
