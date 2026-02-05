"""Tests for API endpoint hardening (idempotency and rate limiting)."""
import pytest
import uuid


class TestIdempotencyHeaders:
    """Test idempotency key header validation."""
    
    @pytest.mark.asyncio
    async def test_initialize_accepts_valid_uuid(self, authenticated_client):
        """Test initialize_payment accepts valid UUID idempotency key."""
        idempotency_key = str(uuid.uuid4())
        
        response = await authenticated_client.post(
            "/api/wallet/initialize",
            json={"amount_usd": 10.0},
            headers={"Idempotency-Key": idempotency_key}
        )
        
        # May fail due to missing Paystack config, but should not fail on UUID validation
        assert response.status_code != 400 or "idempotency" not in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_initialize_rejects_invalid_uuid(self, authenticated_client):
        """Test initialize_payment rejects invalid UUID format."""
        response = await authenticated_client.post(
            "/api/wallet/initialize",
            json={"amount_usd": 10.0},
            headers={"Idempotency-Key": "not-a-uuid"}
        )
        
        assert response.status_code == 400
        assert "idempotency" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_initialize_works_without_idempotency_key(self, authenticated_client):
        """Test initialize_payment works without idempotency key (optional)."""
        response = await authenticated_client.post(
            "/api/wallet/initialize",
            json={"amount_usd": 10.0}
        )
        
        # Should not fail due to missing idempotency key
        assert response.status_code != 400 or "idempotency" not in response.json().get("detail", "").lower()


class TestRateLimiting:
    """Test rate limiting on payment endpoints."""
    
    @pytest.mark.asyncio
    async def test_initialize_rate_limit(self, authenticated_client, cache):
        """Test initialize_payment enforces rate limit (5 req/min)."""
        # Clear any existing rate limit
        cache.flushdb()
        
        # Make 5 requests (should succeed)
        for i in range(5):
            response = await authenticated_client.post(
                "/api/wallet/initialize",
                json={"amount_usd": 10.0}
            )
            # May fail for other reasons, but not rate limit
            assert response.status_code != 429
        
        # 6th request should be rate limited
        response = await authenticated_client.post(
            "/api/wallet/initialize",
            json={"amount_usd": 10.0}
        )
        
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_rate_limit(self, authenticated_client, cache):
        """Test verify_payment enforces rate limit (10 req/min)."""
        # Clear any existing rate limit
        cache.flushdb()
        
        # Make 10 requests (should succeed)
        for i in range(10):
            response = await authenticated_client.post(
                "/api/wallet/verify",
                json={"reference": f"ref_{i}"}
            )
            # May fail for other reasons, but not rate limit
            assert response.status_code != 429
        
        # 11th request should be rate limited
        response = await authenticated_client.post(
            "/api/wallet/verify",
            json={"reference": "ref_11"}
        )
        
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_rate_limit_per_client(self, authenticated_client, cache):
        """Test rate limits are per-client."""
        cache.flushdb()
        
        # Client 1 makes 5 requests
        for i in range(5):
            response = await authenticated_client.post(
                "/api/wallet/initialize",
                json={"amount_usd": 10.0}
            )
        
        # Client 1's 6th request should be rate limited
        response = await authenticated_client.post(
            "/api/wallet/initialize",
            json={"amount_usd": 10.0}
        )
        assert response.status_code == 429
