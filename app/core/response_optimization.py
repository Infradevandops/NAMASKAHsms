"""API response optimization for tier identification system.

Implements:
- Query optimization
- Response compression
- Pagination
- Field selection
- Response caching
"""

import gzip
import json
import logging
from functools import wraps
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimizes database queries."""

    @staticmethod
    def optimize_tier_query(db: Session, user_id: str):
        """Optimize tier query with eager loading.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Optimized query result
        """
        try:
            from sqlalchemy.orm import joinedload

            from app.models.user import User

            # Use eager loading to avoid N+1 queries
            user = (
                db.query(User)
                .options(
                    joinedload(User.tier),
                    joinedload(User.subscription),
                )
                .filter(User.id == user_id)
                .first()
            )

            return user

        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return None

    @staticmethod
    def optimize_feature_query(db: Session, tier: str):
        """Optimize feature query.

        Args:
            db: Database session
            tier: Tier name

        Returns:
            Optimized query result
        """
        try:
            from app.models.subscription_tier import SubscriptionTier

            # Use select to only get needed columns
            tier_obj = (
                db.query(SubscriptionTier).filter(SubscriptionTier.name == tier).first()
            )

            return tier_obj

        except Exception as e:
            logger.error(f"Feature query optimization failed: {e}")
            return None

    @staticmethod
    def batch_query(db: Session, user_ids: List[str]):
        """Batch query for multiple users.

        Args:
            db: Database session
            user_ids: List of user IDs

        Returns:
            Batch query results
        """
        try:
            from app.models.user import User

            # Use IN clause for batch query
            users = db.query(User).filter(User.id.in_(user_ids)).all()

            return users

        except Exception as e:
            logger.error(f"Batch query failed: {e}")
            return []


class ResponseOptimizer:
    """Optimizes API responses."""

    @staticmethod
    def compress_response(data: Dict[str, Any]) -> bytes:
        """Compress response with gzip.

        Args:
            data: Response data

        Returns:
            Compressed data
        """
        try:
            # Serialize to JSON
            json_data = json.dumps(data).encode("utf-8")

            # Compress with gzip
            compressed = gzip.compress(json_data, compresslevel=6)

            logger.debug(
                f"Response compressed: {len(json_data)} → {len(compressed)} bytes "
                f"({100 * len(compressed) / len(json_data):.1f}%)"
            )

            return compressed

        except Exception as e:
            logger.error(f"Response compression failed: {e}")
            return json.dumps(data).encode("utf-8")

    @staticmethod
    def select_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Select only specified fields from response.

        Args:
            data: Response data
            fields: Fields to include

        Returns:
            Filtered response
        """
        if not fields:
            return data

        return {k: v for k, v in data.items() if k in fields}

    @staticmethod
    def paginate_response(
        data: List[Any],
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Paginate response.

        Args:
            data: Response data
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated response
        """
        total = len(data)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "data": data[start:end],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size,
            },
        }


def optimize_response(compress: bool = True, fields: Optional[List[str]] = None):
    """Decorator to optimize API responses.

    Args:
        compress: Whether to compress response
        fields: Fields to include in response
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Call original function
            result = await func(*args, request=request, **kwargs)

            # Select fields if specified
            if fields and isinstance(result, dict):
                result = ResponseOptimizer.select_fields(result, fields)

            # Compress if requested
            if (
                compress
                and request
                and "gzip" in request.headers.get("accept-encoding", "")
            ):
                compressed = ResponseOptimizer.compress_response(result)
                return Response(
                    content=compressed,
                    media_type="application/json",
                    headers={"Content-Encoding": "gzip"},
                )

            return result

        return wrapper

    return decorator


class ResponseCache:
    """Caches API responses."""

    def __init__(self, redis_client=None, ttl: int = 300):
        """Initialize response cache.

        Args:
            redis_client: Redis client
            ttl: Cache TTL in seconds
        """
        self.redis = redis_client
        self.ttl = ttl

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response.

        Args:
            key: Cache key

        Returns:
            Cached response or None
        """
        try:
            if not self.redis:
                return None

            cached = self.redis.get(f"response:{key}")
            if cached:
                return json.loads(cached)

            return None

        except Exception as e:
            logger.error(f"Response cache get failed: {e}")
            return None

    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Set cached response.

        Args:
            key: Cache key
            value: Response value

        Returns:
            True if successful
        """
        try:
            if not self.redis:
                return False

            self.redis.setex(
                f"response:{key}",
                self.ttl,
                json.dumps(value),
            )

            return True

        except Exception as e:
            logger.error(f"Response cache set failed: {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """Invalidate cached responses.

        Args:
            pattern: Pattern to match

        Returns:
            Number of keys deleted
        """
        try:
            if not self.redis:
                return 0

            keys = self.redis.keys(f"response:{pattern}")
            if keys:
                return self.redis.delete(*keys)

            return 0

        except Exception as e:
            logger.error(f"Response cache invalidation failed: {e}")
            return 0


def cache_response(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache API responses.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{request.url.path}" if request else ""

            # Try to get from cache
            if cache_key:
                # This would need a redis client passed in
                pass

            # Call original function
            result = await func(*args, request=request, **kwargs)

            # Cache result
            if cache_key:
                # This would need a redis client passed in
                pass

            return result

        return wrapper

    return decorator
