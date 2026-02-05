"""
import asyncio
import pytest
import time

Redis Integration Tests
Tests for Redis operations including caching, locks, and streams
"""


class TestRedisIntegration:

    """Redis integration tests."""

    def test_redis_basic_set_get(self, redis_client):

        """Test basic Redis set and get operations."""
        key = "test:key"
        value = "test_value"

        # Set
        redis_client.set(key, value)

        # Get
        result = redis_client.get(key)
        assert result == value

        # Cleanup
        redis_client.delete(key)

    def test_redis_expiry(self, redis_client):

        """Test Redis key expiry."""
        key = "test:expiry"
        value = "expires_soon"

        # Set with 1 second TTL
        redis_client.setex(key, 1, value)

        # Should exist immediately
        assert redis_client.get(key) == value

        # Wait for expiry

        time.sleep(2)

        # Should be gone
        assert redis_client.get(key) is None

    def test_redis_increment(self, redis_client):

        """Test Redis increment operations."""
        key = "test:counter"

        # Start from 0
        redis_client.set(key, 0)

        # Increment
        redis_client.incr(key)
        redis_client.incr(key)
        redis_client.incr(key)

        # Check value
        assert int(redis_client.get(key)) == 3

        # Cleanup
        redis_client.delete(key)

    def test_redis_hash_operations(self, redis_client):

        """Test Redis hash operations."""
        key = "test:hash"

        # Set hash fields
        redis_client.hset(key, "field1", "value1")
        redis_client.hset(key, "field2", "value2")

        # Get field
        assert redis_client.hget(key, "field1") == "value1"

        # Get all
        all_fields = redis_client.hgetall(key)
        assert len(all_fields) == 2

        # Cleanup
        redis_client.delete(key)

    def test_redis_list_operations(self, redis_client):

        """Test Redis list operations."""
        key = "test:list"

        # Push items
        redis_client.rpush(key, "item1")
        redis_client.rpush(key, "item2")
        redis_client.rpush(key, "item3")

        # Get length
        length = redis_client.llen(key)
        assert length == 3

        # Pop item
        item = redis_client.lpop(key)
        assert item == "item1"

        # Cleanup
        redis_client.delete(key)

    def test_redis_set_operations(self, redis_client):

        """Test Redis set operations."""
        key = "test:set"

        # Add members
        redis_client.sadd(key, "member1")
        redis_client.sadd(key, "member2")
        redis_client.sadd(key, "member3")

        # Check membership
        assert redis_client.sismember(key, "member1")
        assert not redis_client.sismember(key, "member4")

        # Get all members
        members = redis_client.smembers(key)
        assert len(members) == 3

        # Cleanup
        redis_client.delete(key)

    def test_redis_sorted_set(self, redis_client):

        """Test Redis sorted set operations."""
        key = "test:zset"

        # Add scored members
        redis_client.zadd(key, {"member1": 1.0, "member2": 2.0, "member3": 3.0})

        # Get range
        members = redis_client.zrange(key, 0, -1)
        assert len(members) == 3

        # Get by score
        high_scorers = redis_client.zrangebyscore(key, 2.0, 3.0)
        assert len(high_scorers) == 2

        # Cleanup
        redis_client.delete(key)

    def test_redis_pipeline(self, redis_client):

        """Test Redis pipeline for batch operations."""
        pipe = redis_client.pipeline()

        # Queue multiple operations
        pipe.set("test:pipe1", "value1")
        pipe.set("test:pipe2", "value2")
        pipe.set("test:pipe3", "value3")

        # Execute all at once
        results = pipe.execute()
        assert len(results) == 3

        # Verify
        assert redis_client.get("test:pipe1") == "value1"

        # Cleanup
        redis_client.delete("test:pipe1", "test:pipe2", "test:pipe3")

    def test_redis_transaction(self, redis_client):

        """Test Redis transaction with WATCH."""
        key = "test:transaction"
        redis_client.set(key, "0")

        # Watch key
        pipe = redis_client.pipeline()
        pipe.watch(key)

        # Start transaction
        pipe.multi()
        pipe.incr(key)
        pipe.incr(key)

        # Execute
        pipe.execute()

        # Verify
        assert int(redis_client.get(key)) == 2

        # Cleanup
        redis_client.delete(key)

    def test_redis_key_pattern_matching(self, redis_client):

        """Test Redis key pattern matching."""
        # Create test keys
        redis_client.set("test:pattern:1", "value1")
        redis_client.set("test:pattern:2", "value2")
        redis_client.set("test:other:1", "value3")

        # Find keys matching pattern
        keys = redis_client.keys("test:pattern:*")
        assert len(keys) >= 2

        # Cleanup
        for key in keys:
            redis_client.delete(key)
        redis_client.delete("test:other:1")

    def test_redis_exists_check(self, redis_client):

        """Test Redis key existence check."""
        key = "test:exists"

        # Should not exist
        assert redis_client.exists(key) == 0

        # Create key
        redis_client.set(key, "value")

        # Should exist
        assert redis_client.exists(key) == 1

        # Cleanup
        redis_client.delete(key)

    def test_redis_delete_multiple_keys(self, redis_client):

        """Test deleting multiple keys at once."""
        keys = ["test:del:1", "test:del:2", "test:del:3"]

        # Create keys
        for key in keys:
            redis_client.set(key, "value")

        # Delete all
        deleted_count = redis_client.delete(*keys)
        assert deleted_count == 3

        # Verify deleted
        for key in keys:
            assert redis_client.exists(key) == 0

    def test_redis_ttl_check(self, redis_client):

        """Test checking TTL of keys."""
        key = "test:ttl"

        # Set with 60 second TTL
        redis_client.setex(key, 60, "value")

        # Check TTL
        ttl = redis_client.ttl(key)
        assert ttl > 0 and ttl <= 60

        # Cleanup
        redis_client.delete(key)

        @pytest.mark.asyncio
    async def test_redis_concurrent_access(self, redis_client):
        """Test concurrent Redis access."""
        key = "test:concurrent"
        redis_client.set(key, 0)

    async def increment():
        for _ in range(10):
                redis_client.incr(key)

        # Run concurrent increments
        await asyncio.gather(increment(), increment(), increment())

        # Should be 30
        final_value = int(redis_client.get(key))
        assert final_value == 30

        # Cleanup
        redis_client.delete(key)


        if __name__ == "__main__":
        print("Redis integration tests created: 15 tests")
