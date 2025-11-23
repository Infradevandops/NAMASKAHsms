"""Integration tests for TextVerified API."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.textverified_auth import TextVerifiedAuthService


@pytest.mark.asyncio
async def test_textverified_authentication():
    """Test TextVerified authentication."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "bearer_token": "test_token_123",
            "expires_in": 900,
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        auth_service = TextVerifiedAuthService()
        token = await auth_service.authenticate()

        assert token == "test_token_123"
        assert auth_service.bearer_token == "test_token_123"


@pytest.mark.asyncio
async def test_textverified_get_balance():
    """Test getting account balance."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "balance": 100.50,
            "currency": "USD",
            "id": "account_123",
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        with patch.object(
            TextVerifiedAuthService, "get_headers", new_callable=AsyncMock
        ) as mock_headers:
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            client = TextVerifiedAPIClient()
            result = await client.get_account_balance()

            assert result["balance"] == 100.50
            assert result["currency"] == "USD"


@pytest.mark.asyncio
async def test_textverified_create_verification():
    """Test creating verification."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "id": "ver_123",
            "number": "+1234567890",
            "cost": 0.50,
            "status": "pending",
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        with patch.object(
            TextVerifiedAuthService, "get_headers", new_callable=AsyncMock
        ) as mock_headers:
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            client = TextVerifiedAPIClient()
            result = await client.create_verification("telegram")

            assert result["id"] == "ver_123"
            assert result["phone_number"] == "+1234567890"
            assert result["cost"] == 0.50


@pytest.mark.asyncio
async def test_textverified_get_sms_messages():
    """Test getting SMS messages."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "messages": [
                {
                    "id": "sms_123",
                    "text": "Your code is 12345",
                    "from": "+1234567890",
                    "received_at": "2024-01-01T10:00:00Z",
                }
            ]
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        with patch.object(
            TextVerifiedAuthService, "get_headers", new_callable=AsyncMock
        ) as mock_headers:
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            client = TextVerifiedAPIClient()
            messages = await client.get_sms_messages("res_123")

            assert len(messages) == 1
            assert messages[0]["text"] == "Your code is 12345"


@pytest.mark.asyncio
async def test_textverified_create_rental():
    """Test creating rental."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "id": "rental_123",
            "number": "+1234567890",
            "cost": 5.00,
            "expires_at": "2024-02-01T10:00:00Z",
            "renewable": True,
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        with patch.object(
            TextVerifiedAuthService, "get_headers", new_callable=AsyncMock
        ) as mock_headers:
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            client = TextVerifiedAPIClient()
            result = await client.create_rental("telegram", 30, True)

            assert result["id"] == "rental_123"
            assert result["phone_number"] == "+1234567890"
            assert result["renewable"] is True


@pytest.mark.asyncio
async def test_textverified_integration_caching():
    """Test integration service caching."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "services": [
                {"id": "telegram", "name": "Telegram", "category": "messaging"}
            ]
        }
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        with patch.object(
            TextVerifiedAuthService, "get_headers", new_callable=AsyncMock
        ) as mock_headers:
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            with patch("app.core.cache_manager.cache_manager") as mock_cache:
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock()

                integration = TextVerifiedIntegration()
                services = await integration.get_services_list()

                assert len(services) == 1
                assert services[0]["name"] == "Telegram"
                mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_retry():
    """Test error handling with retry logic."""

    attempt_count = 0

    @retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.01))
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary error")
        return "success"

    result = await failing_function()
    assert result == "success"
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_api_error_handler():
    """Test API error handler."""

    # Test user-friendly messages
    msg_401 = APIErrorHandler.get_user_message(401)
    assert "Authentication" in msg_401

    msg_429 = APIErrorHandler.get_user_message(429)
    assert "Rate limit" in msg_429

    # Test retryable errors
    assert APIErrorHandler.is_retryable(429) is True
    assert APIErrorHandler.is_retryable(500) is True
    assert APIErrorHandler.is_retryable(401) is False
