"""Tests for unified cache system."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.core.unified_cache import UnifiedCacheManager, InMemoryCache


class TestInMemoryCache:
    """Test in - memory cache functionality."""

    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations."""
        cache = InMemoryCache()

        # Test set and get
        await cache.set("test_key", "test_value", ttl=3600)
        result = await cache.get("test_key")
        assert result == "test_value"

        # Test non - existent key
        result = await cache.get("nonexistent")
        assert result is None

        # Test delete
        await cache.delete("test_key")
        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = InMemoryCache()

        # Set with very short TTL
        await cache.set("expire_key", "expire_value", ttl=0.1)

        # Should be available immediately
        result = await cache.get("expire_key")
        assert result == "expire_value"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        result = await cache.get("expire_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing all cache."""
        cache = InMemoryCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Verify keys exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

        # Clear cache
        await cache.clear()

        # Verify keys are gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_keys_pattern_matching(self):
        """Test pattern matching for keys."""
        cache = InMemoryCache()

        await cache.set("user:123", "data1")
        await cache.set("user:456", "data2")
        await cache.set("service:abc", "data3")

        # Test pattern matching
        user_keys = await cache.keys("user:*")
        assert len(user_keys) == 2
        assert "user:123" in user_keys
        assert "user:456" in user_keys

        service_keys = await cache.keys("service:*")
        assert len(service_keys) == 1
        assert "service:abc" in service_keys


class TestUnifiedCacheManager:
    """Test unified cache manager."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance."""
        return UnifiedCacheManager()

    @pytest.mark.asyncio
    async def test_memory_fallback(self, cache_manager):
        """Test fallback to memory cache when Redis unavailable."""
        # Don't connect to Redis (simulate unavailable)
        cache_manager._connected = True
        cache_manager.redis_client = None

        # Should use memory cache
        await cache_manager.set("test_key", "test_value")
        result = await cache_manager.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    @patch('redis.asyncio.from_url')
    async def test_redis_connection_success(self, mock_redis, cache_manager):
        """Test successful Redis connection."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_redis.return_value = mock_client

        await cache_manager.connect()

        assert cache_manager._connected is True
        assert cache_manager.redis_client is not None
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    @patch('redis.asyncio.from_url')
    async def test_redis_connection_failure(self, mock_redis, cache_manager):
        """Test Redis connection failure fallback."""
        mock_redis.side_effect = Exception("Connection failed")

        await cache_manager.connect()

        assert cache_manager._connected is True
        assert cache_manager.redis_client is None

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache_manager):
        """Test cache key generation."""
        key = cache_manager.cache_key("user", "123", "profile")
        assert key == "user:123:profile"

        key = cache_manager.cache_key("service")
        assert key == "service:"

    @pytest.mark.asyncio
    async def test_ttl_defaults(self, cache_manager):
        """Test TTL default values."""
        assert cache_manager.ttl_defaults["countries"] == 86400
        assert cache_manager.ttl_defaults["services"] == 3600
        assert cache_manager.ttl_defaults["verification"] == 300
        assert cache_manager.ttl_defaults["user"] == 1800
        assert cache_manager.ttl_defaults["default"] == 3600

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, cache_manager):
        """Test pattern - based cache invalidation."""
        # Setup cache manager with memory only
        cache_manager._connected = True
        cache_manager.redis_client = None

        # Set some test data
        await cache_manager.set("user:123:profile", {"name": "John"})
        await cache_manager.set("user:123:stats", {"count": 5})
        await cache_manager.set("user:456:profile", {"name": "Jane"})
        await cache_manager.set("service:telegram", {"price": 0.5})

        # Verify data exists
        assert await cache_manager.get("user:123:profile") is not None
        assert await cache_manager.get("user:123:stats") is not None
        assert await cache_manager.get("user:456:profile") is not None
        assert await cache_manager.get("service:telegram") is not None

        # Invalidate user:123 pattern
        await cache_manager.invalidate_pattern("user:123*")

        # Verify user:123 data is gone but others remain
        assert await cache_manager.get("user:123:profile") is None
        assert await cache_manager.get("user:123:stats") is None
        assert await cache_manager.get("user:456:profile") is not None
        assert await cache_manager.get("service:telegram") is not None

    @pytest.mark.asyncio
    async def test_cached_decorator(self, cache_manager):
        """Test cached decorator functionality."""
        call_count = 0

        @cache_manager.cached(ttl=3600, key_prefix="test_func")
        async def expensive_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            return f"result_{arg1}_{arg2}"

        # First call should execute function
        result1 = await expensive_function("a", "b")
        assert result1 == "result_a_b"
        assert call_count == 1

        # Second call should use cache
        result2 = await expensive_function("a", "b")
        assert result2 == "result_a_b"
        assert call_count == 1  # Should not increment

        # Different args should execute function again
        result3 = await expensive_function("c", "d")
        assert result3 == "result_c_d"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_on_change_decorator(self, cache_manager):
        """Test invalidate on change decorator."""
        # Setup some cached data
        await cache_manager.set("user:123:profile", {"name": "John"})
        await cache_manager.set("user:123:stats", {"count": 5})

        @cache_manager.invalidate_on_change("user:123*")
        async def update_user_data():
            return "updated"

        # Verify data exists before
        assert await cache_manager.get("user:123:profile") is not None
        assert await cache_manager.get("user:123:stats") is not None

        # Call function with decorator
        result = await update_user_data()
        assert result == "updated"

        # Verify data is invalidated after
        assert await cache_manager.get("user:123:profile") is None
        assert await cache_manager.get("user:123:stats") is None

    @pytest.mark.asyncio
    async def test_get_stats_memory_only(self, cache_manager):
        """Test getting stats with memory cache only."""
        cache_manager._connected = True
        cache_manager.redis_client = None

        # Add some data to memory cache
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")

        stats = await cache_manager.get_stats()

        assert stats["redis_connected"] is False
        assert stats["memory_keys"] == 2

    @pytest.mark.asyncio
    @patch('redis.asyncio.Redis')
    async def test_get_stats_with_redis(self, mock_redis_class, cache_manager):
        """Test getting stats with Redis connected."""
        mock_redis = AsyncMock()
        mock_redis.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000
        }
        cache_manager.redis_client = mock_redis

        stats = await cache_manager.get_stats()

        assert stats["redis_connected"] is True
        assert stats["redis_used_memory"] == "1.5M"
        assert stats["redis_connected_clients"] == 5
        assert stats["redis_total_commands"] == 1000


class TestCacheConvenienceFunctions:
    """Test convenience functions for common caching patterns."""

    @pytest.mark.asyncio
    async def test_cache_countries(self):
        """Test caching countries data."""

        countries_data = [{"code": "US", "name": "United States"}]
        await cache_countries(countries_data)

        result = await cache.get("countries:all")
        assert result == countries_data

    @pytest.mark.asyncio
    async def test_cache_services(self):
        """Test caching services data."""

        services_data = [{"name": "telegram", "price": 0.5}]
        await cache_services("US", services_data)

        result = await cache.get("services:US")
        assert result == services_data

    @pytest.mark.asyncio
    async def test_cache_user_data(self):
        """Test caching user data."""

        user_data = {"name": "John", "credits": 10.0}
        await cache_user_data("123", user_data)

        result = await cache.get("user:123")
        assert result == user_data

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self):
        """Test invalidating user cache."""

        # Set up user - related cache data
        await cache.set("user:123:profile", {"name": "John"})
        await cache.set("user:123:stats", {"count": 5})
        await cache.set("verification:123:abc", {"status": "pending"})
        await cache.set("user:456:profile", {"name": "Jane"})

        # Invalidate user 123 cache
        await invalidate_user_cache("123")

        # Verify user 123 data is gone
        assert await cache.get("user:123:profile") is None
        assert await cache.get("user:123:stats") is None
        assert await cache.get("verification:123:abc") is None

        # Verify other user data remains
        assert await cache.get("user:456:profile") is not None

    @pytest.mark.asyncio
    async def test_cache_verification(self):
        """Test caching verification data."""

        verification_data = {"status": "pending", "phone": "+1234567890"}
        await cache_verification("abc123", verification_data)

        result = await cache.get("verification:abc123")
        assert result == verification_data

    @pytest.mark.asyncio
    async def test_cache_provider_data(self):
        """Test caching provider data."""

        provider_data = {"balance": 100.0, "status": "healthy"}
        await cache_provider_data("textverified", "balance", provider_data)

        result = await cache.get("provider:textverified:balance")
        assert result == provider_data


class TestCacheIntegration:
    """Integration tests for cache system."""

    @pytest.mark.asyncio
    async def test_redis_fallback_behavior(self):
        """Test behavior when Redis fails during operation."""

        # Start with Redis unavailable
        cache.redis_client = None
        cache._connected = True

        # Should work with memory cache
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        assert result == "test_value"

        # Simulate Redis becoming available
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"cached": "from_redis"}'
        mock_redis.setex = AsyncMock()
        cache.redis_client = mock_redis

        # Should now use Redis
        await cache.set("redis_key", {"cached": "from_redis"})
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_integration(self):
        """Test decorator integration with cache system."""

        execution_count = 0

        @cache.cached(ttl=300, key_prefix="integration_test")
        async def fetch_data(user_id: str):
            nonlocal execution_count
            execution_count += 1
            return {"user_id": user_id, "data": f"fetched_{execution_count}"}

        # First call
        result1 = await fetch_data("123")
        assert result1["user_id"] == "123"
        assert execution_count == 1

        # Second call should use cache
        result2 = await fetch_data("123")
        assert result2 == result1
        assert execution_count == 1

        # Invalidate and call again
        await cache.invalidate_pattern("integration_test:*")
        result3 = await fetch_data("123")
        assert result3["user_id"] == "123"
        assert execution_count == 2
