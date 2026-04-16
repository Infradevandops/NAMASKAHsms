"""Unit tests for TextVerified adapter."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.textverified_adapter import TextVerifiedAdapter
from app.services.providers.base_provider import PurchaseResult, MessageResult


class TestTextVerifiedAdapter:
    """Test suite for TextVerifiedAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        with patch("app.services.providers.textverified_adapter.TextVerifiedService"):
            return TextVerifiedAdapter()

    @pytest.fixture
    def mock_service(self, adapter):
        """Mock TextVerifiedService."""
        return adapter._service

    def test_name_property(self, adapter):
        """Should return 'textverified' as name."""
        assert adapter.name == "textverified"

    def test_enabled_property_when_service_enabled(self, adapter, mock_service):
        """Should return True when service is enabled."""
        mock_service.enabled = True
        assert adapter.enabled is True

    def test_enabled_property_when_service_disabled(self, adapter, mock_service):
        """Should return False when service is disabled."""
        mock_service.enabled = False
        assert adapter.enabled is False

    @pytest.mark.asyncio
    async def test_purchase_number_success(self, adapter, mock_service):
        """Should successfully purchase number and return PurchaseResult."""
        mock_service.create_verification = AsyncMock(
            return_value={
                "id": "tv123",
                "phone_number": "+12025551234",
                "cost": 2.22,
                "ends_at": "2026-03-26T12:00:00Z",
                "area_code_matched": True,
                "carrier_matched": True,
                "real_carrier": "verizon",
                "voip_rejected": False,
                "fallback_applied": False,
                "requested_area_code": "202",
                "assigned_area_code": "202",
                "same_state_fallback": True,
                "retry_attempts": 0,
                "tv_object": MagicMock(),
            }
        )

        result = await adapter.purchase_number(
            service="whatsapp",
            country="US",
            area_code="202",
            carrier="verizon",
        )

        assert isinstance(result, PurchaseResult)
        assert result.phone_number == "+12025551234"
        assert result.order_id == "tv123"
        assert result.cost == 2.22
        assert result.provider == "textverified"
        assert result.area_code_matched is True
        assert result.carrier_matched is True
        assert result.real_carrier == "verizon"

    @pytest.mark.asyncio
    async def test_purchase_number_failure(self, adapter, mock_service):
        """Should raise RuntimeError on purchase failure."""
        mock_service.create_verification = AsyncMock(side_effect=Exception("API error"))

        with pytest.raises(RuntimeError, match="TextVerified purchase failed"):
            await adapter.purchase_number(
                service="whatsapp",
                country="US",
            )

    @pytest.mark.asyncio
    async def test_check_messages_with_messages(self, adapter, mock_service):
        """Should return MessageResult list when messages exist."""
        mock_service.check_sms = AsyncMock(
            return_value={
                "status": "COMPLETED",
                "messages": [{"text": "Your code is 123456", "code": "123456"}],
            }
        )

        messages = await adapter.check_messages("tv123")

        assert len(messages) == 1
        assert isinstance(messages[0], MessageResult)
        assert messages[0].text == "Your code is 123456"
        assert messages[0].code == "123456"

    @pytest.mark.asyncio
    async def test_check_messages_no_messages(self, adapter, mock_service):
        """Should return empty list when no messages."""
        mock_service.check_sms = AsyncMock(
            return_value={"status": "PENDING", "messages": []}
        )

        messages = await adapter.check_messages("tv123")

        assert messages == []

    @pytest.mark.asyncio
    async def test_check_messages_error(self, adapter, mock_service):
        """Should return empty list on error."""
        mock_service.check_sms = AsyncMock(side_effect=Exception("API error"))

        messages = await adapter.check_messages("tv123")

        assert messages == []

    @pytest.mark.asyncio
    async def test_report_failed(self, adapter, mock_service):
        """Should call report_verification."""
        mock_service.report_verification = AsyncMock(return_value=True)

        result = await adapter.report_failed("tv123")

        assert result is True
        mock_service.report_verification.assert_called_once_with("tv123")

    @pytest.mark.asyncio
    async def test_cancel(self, adapter, mock_service):
        """Should call _cancel_safe."""
        mock_service._cancel_safe = AsyncMock(return_value=True)

        result = await adapter.cancel("tv123")

        assert result is True
        mock_service._cancel_safe.assert_called_once_with("tv123")

    @pytest.mark.asyncio
    async def test_get_balance(self, adapter, mock_service):
        """Should return balance from service."""
        mock_service.get_balance = AsyncMock(return_value={"balance": 100.50})

        balance = await adapter.get_balance()

        assert balance == 100.50

    @pytest.mark.asyncio
    async def test_get_balance_default_zero(self, adapter, mock_service):
        """Should return 0.0 if balance not in response."""
        mock_service.get_balance = AsyncMock(return_value={})

        balance = await adapter.get_balance()

        assert balance == 0.0
