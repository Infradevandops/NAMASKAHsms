"""Performance optimization utilities."""
import asyncio
from functools import wraps
from app.core.caching import cache


def async_cache(ttl: int = 300):
    """Async function caching decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached:
                return cached

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


async def batch_database_operations(operations: list):
    """Batch multiple database operations for better performance."""
    return await asyncio.gather(*operations, return_exceptions=True)
