"""Rate limiting middleware for API endpoints."""
import time
from functools import wraps
from typing import Callable
from fastapi import HTTPException, Request
from app.core.cache import get_redis
from app.core.logging import get_logger

logger = get_logger(__name__)


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limit decorator for FastAPI endpoints.
    
    Args:
        max_requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get client identifier (IP or user ID)
            client_id = request.client.host if request.client else "unknown"
            
            # Try to get user ID from headers for authenticated requests
            auth_header = request.headers.get("authorization")
            if auth_header:
                client_id = f"user_{auth_header[:20]}"  # Use part of auth token
            
            # Create rate limit key
            key = f"rate_limit:{func.__name__}:{client_id}"
            
            try:
                redis = get_redis()
                
                # Get current count
                current = redis.get(key)
                
                if current is None:
                    # First request in window
                    redis.setex(key, window_seconds, 1)
                    return await func(*args, **kwargs)
                
                current_count = int(current)
                
                if current_count >= max_requests:
                    logger.warning(f"Rate limit exceeded for {client_id} on {func.__name__}")
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds"
                    )
                
                # Increment counter
                redis.incr(key)
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                # If Redis fails, allow request but log error
                logger.error(f"Rate limiting error: {e}")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
