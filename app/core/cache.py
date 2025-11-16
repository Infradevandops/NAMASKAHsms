"""Simple in-memory cache for API responses."""
import time
from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        # Check if expired
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return self._cache[key]
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache with TTL in seconds."""
        self._cache[key] = value
        self._expiry[key] = time.time() + expire
        logger.debug(f"Cache set: {key} (expires in {expire}s)")
    
    async def delete(self, key: str):
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
        logger.debug(f"Cache deleted: {key}")
    
    async def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._expiry.clear()
        logger.info("Cache cleared")


# Global cache instance
cache = SimpleCache()
