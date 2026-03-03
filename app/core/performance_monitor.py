"""Performance monitoring utilities - WITH ERROR HANDLING."""


import time

from prometheus_client import Counter, Histogram

from app.core.logging import get_logger

logger = get_logger(__name__)

request_duration = Histogram("request_duration_seconds", "Request duration in seconds", ["method", "endpoint"])
db_query_duration = Histogram("db_query_duration_seconds", "Database query duration in seconds", ["query_type"])
cache_hits = Counter("cache_hits_total", "Total cache hits", ["cache_type"])
cache_misses = Counter("cache_misses_total", "Total cache misses", ["cache_type"])


class PerformanceMonitor:
    """Monitor performance metrics."""

    @staticmethod
    def track_request(method: str, endpoint: str):
        """Decorator to track request duration."""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            return wrapper

        return decorator

    @staticmethod
    def track_db_query(query_type: str):
        """Decorator to track database query duration."""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    db_query_duration.labels(query_type=query_type).observe(duration)

            return wrapper

        return decorator
