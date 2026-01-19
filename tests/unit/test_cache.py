import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.unified_cache import InMemoryCache, UnifiedCacheManager


@pytest.mark.asyncio
async def test_in_memory_cache():
    cache = InMemoryCache()
    await cache.set("key", "value", ttl=10)
    assert await cache.get("key") == "value"

    await cache.delete("key")
    assert await cache.get("key") is None

    await cache.set("key2", "value2")
    await cache.clear()
    assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_unified_cache_manager():
    manager = UnifiedCacheManager()

    # Test fallback to memory
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis.side_effect = Exception("Redis Down")
        await manager.connect()
        assert manager.redis_client is None

        await manager.set("test_key", {"data": 123})
        assert await manager.get("test_key") == {"data": 123}


@pytest.mark.asyncio
async def test_unified_cache_with_mock_redis():
    manager = UnifiedCacheManager()
    manager.redis_client = AsyncMock()
    manager._connected = True

    # Test set
    await manager.set("k", "v")
    manager.redis_client.setex.assert_called()

    # Test get
    manager.redis_client.get.return_value = json.dumps("v")
    assert await manager.get("k") == "v"
