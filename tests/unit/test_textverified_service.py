"""Tests for TextVerified Service - Critical SMS Operations

This test suite covers the most critical SMS verification operations:
- Number purchasing
- SMS polling and retrieval
- Verification cancellation
- Service availability
- Area code handling
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.textverified_service import TextVerifiedService


@pytest.fixture
def mock_textverified_client():
    """Mock TextVerified client."""
    client = Mock()
    client.account = Mock()
    client.services = Mock()
    client.verifications = Mock()
    client.sms = Mock()
    client.reservations = Mock()
    return client


@pytest.fixture
def textverified_service(mock_textverified_client):
    """Create TextVerifiedService instance with mocked client."""
    with patch.dict(
        "os.environ",
        {
            "TEXTVERIFIED_API_KEY": "test_key",
            "TEXTVERIFIED_USERNAME": "test_user",
        },
    ):
        service = TextVerifiedService()
        service.client = mock_textverified_client
        service.enabled = True
        return service


@pytest.fixture
def mock_verification():
    """Create a mock verification object."""
    verification = Mock()
    verification.id = "ver123"
    verification.number = "+12025551234"
    verification.total_cost = 2.50
    verification.ends_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    verification.created_at = datetime.now(timezone.utc)
    verification.state = Mock(value="active")
    return verification


@pytest.fixture
def mock_sms():
    """Create a mock SMS object."""
    sms = Mock()
    sms.sms_content = "Your verification code is 123456"
    sms.parsed_code = "123456"
    sms.created_at = datetime.now(timezone.utc)
    return sms


class TestServiceInitialization:
    """Test service initialization and configuration."""

    def test_service_enabled_with_credentials(self):
        """Test service is enabled when credentials are provided."""
        with patch.dict(
            "os.environ",
            {
                "TEXTVERIFIED_API_KEY": "test_key",
                "TEXTVERIFIED_USERNAME": "test_user",
            },
        ):
            service = TextVerifiedService()
            assert service.enabled is True
            assert service.api_key == "test_key"

    def test_service_disabled_without_credentials(self):
        """Test service is disabled when credentials are missing."""
        with patch.dict("os.environ", {}, clear=True):
            service = TextVerifiedService()
            assert service.enabled is False
            assert service.client is None


class TestBalanceOperations:
    """Test balance retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_balance_success(self, textverified_service):
        """Test successful balance retrieval."""
        textverified_service.client.account.balance = 100.50

        result = await textverified_service.get_balance()

        assert result["balance"] == 100.50
        assert result["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_balance_service_disabled(self):
        """Test balance retrieval when service is disabled."""
        service = TextVerifiedService()
        service.enabled = False

        result = await service.get_balance()

        assert result["balance"] == 0.0
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_balance_api_error(self, textverified_service):
        """Test balance retrieval when API fails."""
        textverified_service.client.account.balance = Mock(
            side_effect=Exception("API error")
        )

        result = await textverified_service.get_balance()

        assert result["balance"] == 0.0
        assert "error" in result


class TestServicesList:
    """Test services list retrieval."""

    @pytest.mark.asyncio
    async def test_get_services_list_success(self, textverified_service):
        """Test successful services list retrieval."""
        mock_service = Mock()
        mock_service.service_name = "whatsapp"
        textverified_service.client.services.list.return_value = [mock_service]

        with patch("app.core.unified_cache.cache.get", return_value=None):
            with patch("app.core.unified_cache.cache.set"):
                result = await textverified_service.get_services_list()

        assert len(result) > 0
        assert result[0]["id"] == "whatsapp"

    @pytest.mark.asyncio
    async def test_get_services_list_from_cache(self, textverified_service):
        """Test services list retrieval from cache."""
        cached_services = [
            {"id": "whatsapp", "name": "WhatsApp", "price": 2.50, "cost": 2.50}
        ]

        with patch("app.core.unified_cache.cache.get", return_value=cached_services):
            result = await textverified_service.get_services_list()

        assert result == cached_services
        # Should not call API
        assert not textverified_service.client.services.list.called

    @pytest.mark.asyncio
    async def test_get_services_list_service_disabled(self):
        """Test services list when service is disabled."""
        service = TextVerifiedService()
        service.enabled = False

        with pytest.raises(RuntimeError, match="TextVerified API is not configured"):
            await service.get_services_list()


class TestNumberPurchasing:
    """Test number purchasing operations - CRITICAL for core product."""

    @pytest.mark.asyncio
    async def test_purchase_number_success(
        self, textverified_service, mock_verification
    ):
        """Test successful number purchase."""
        textverified_service.client.verifications.create.return_value = (
            mock_verification
        )

        with patch(
            "app.services.textverified_service.PhoneValidator"
        ) as mock_validator:
            mock_validator.return_value.validate_mobile.return_value = {
                "is_mobile": True,
                "is_voip": False,
            }

            result = await textverified_service.purchase_number(
                service="whatsapp", country="US"
            )

        assert result["success"] is True
        assert result["verification_id"] == "ver123"
        assert result["phone_number"] == "+12025551234"
        assert "cost" in result

    @pytest.mark.asyncio
    async def test_purchase_number_with_area_code(
        self, textverified_service, mock_verification
    ):
        """Test number purchase with specific area code."""
        textverified_service.client.verifications.create.return_value = (
            mock_verification
        )

        with patch(
            "app.services.textverified_service.PhoneValidator"
        ) as mock_validator:
            mock_validator.return_value.validate_mobile.return_value = {
                "is_mobile": True,
                "is_voip": False,
            }
            with patch.object(
                textverified_service,
                "_build_area_code_preference",
                return_value=["202"],
            ):
                result = await textverified_service.purchase_number(
                    service="whatsapp", country="US", area_code="202"
                )

        assert result["success"] is True
        assert result["requested_area_code"] == "202"

    @pytest.mark.asyncio
    async def test_purchase_number_voip_rejection(
        self, textverified_service, mock_verification
    ):
        """Test number purchase rejects VOIP numbers."""
        textverified_service.client.verifications.create.return_value = (
            mock_verification
        )

        with patch(
            "app.services.textverified_service.PhoneValidator"
        ) as mock_validator:
            # First attempt returns VOIP, second returns mobile
            mock_validator.return_value.validate_mobile.side_effect = [
                {"is_mobile": False, "is_voip": True, "number_type": "voip"},
                {"is_mobile": True, "is_voip": False, "number_type": "mobile"},
            ]

            with patch.object(textverified_service, "_cancel_safe", return_value=True):
                result = await textverified_service.purchase_number(
                    service="whatsapp", country="US"
                )

        assert result["success"] is True
        # Should have retried
        assert textverified_service.client.verifications.create.call_count >= 2

    @pytest.mark.asyncio
    async def test_purchase_number_api_error(self, textverified_service):
        """Test number purchase when API fails."""
        textverified_service.client.verifications.create.side_effect = Exception(
            "API error"
        )

        result = await textverified_service.purchase_number(
            service="whatsapp", country="US"
        )

        assert result["success"] is False
        assert "error" in result


class TestSMSRetrieval:
    """Test SMS retrieval operations - CRITICAL for core product."""

    @pytest.mark.asyncio
    async def test_get_sms_success(self, textverified_service, mock_sms):
        """Test successful SMS retrieval."""
        textverified_service.client.sms.list.return_value = [mock_sms]

        result = await textverified_service.get_sms("ver123")

        assert result["success"] is True
        assert result["code"] == "123456"
        assert "Your verification code" in result["sms"]

    @pytest.mark.asyncio
    async def test_get_sms_no_messages(self, textverified_service):
        """Test SMS retrieval when no messages available."""
        textverified_service.client.sms.list.return_value = []

        result = await textverified_service.get_sms("ver123")

        assert result["success"] is False
        assert result["sms"] is None

    @pytest.mark.asyncio
    async def test_get_sms_filters_stale_messages(self, textverified_service):
        """Test SMS retrieval filters out stale messages from recycled numbers."""
        old_sms = Mock()
        old_sms.sms_content = "Old code: 111111"
        old_sms.parsed_code = "111111"
        old_sms.created_at = datetime.now(timezone.utc) - timedelta(hours=2)

        new_sms = Mock()
        new_sms.sms_content = "New code: 222222"
        new_sms.parsed_code = "222222"
        new_sms.created_at = datetime.now(timezone.utc)

        textverified_service.client.sms.list.return_value = [old_sms, new_sms]

        created_after = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = await textverified_service.get_sms(
            "ver123", created_after=created_after
        )

        assert result["success"] is True
        assert result["code"] == "222222"  # Should get new SMS only

    @pytest.mark.asyncio
    async def test_get_sms_service_disabled(self):
        """Test SMS retrieval when service is disabled."""
        service = TextVerifiedService()
        service.enabled = False

        result = await service.get_sms("ver123")

        assert result["success"] is False
        assert "error" in result


class TestSMSPolling:
    """Test SMS polling operations."""

    @pytest.mark.asyncio
    async def test_poll_sms_standard_success(
        self, textverified_service, mock_verification, mock_sms
    ):
        """Test successful SMS polling."""

        def mock_incoming(*args, **kwargs):
            yield mock_sms

        textverified_service.client.sms.incoming = mock_incoming

        result = await textverified_service.poll_sms_standard(
            mock_verification, timeout_seconds=10.0
        )

        assert result["success"] is True
        assert result["code"] == "123456"

    @pytest.mark.asyncio
    async def test_poll_sms_standard_timeout(
        self, textverified_service, mock_verification
    ):
        """Test SMS polling timeout."""

        def mock_incoming(*args, **kwargs):
            return iter([])  # No messages

        textverified_service.client.sms.incoming = mock_incoming

        result = await textverified_service.poll_sms_standard(
            mock_verification, timeout_seconds=1.0
        )

        assert result["success"] is False
        assert result.get("timed_out") is True


class TestVerificationCancellation:
    """Test verification cancellation operations."""

    @pytest.mark.asyncio
    async def test_cancel_verification_success(self, textverified_service):
        """Test successful verification cancellation."""
        textverified_service.client.verifications.cancel.return_value = None

        result = await textverified_service.cancel_verification("ver123")

        assert result["success"] is True
        assert textverified_service.client.verifications.cancel.called

    @pytest.mark.asyncio
    async def test_cancel_verification_api_error(self, textverified_service):
        """Test verification cancellation when API fails."""
        textverified_service.client.verifications.cancel.side_effect = Exception(
            "API error"
        )

        result = await textverified_service.cancel_verification("ver123")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_cancel_safe_no_exception(self, textverified_service):
        """Test _cancel_safe never raises exceptions."""
        textverified_service.client.verifications.cancel.side_effect = Exception(
            "API error"
        )

        # Should not raise exception
        result = await textverified_service._cancel_safe("ver123")

        assert result is False  # Returns False on failure


class TestVerificationReporting:
    """Test verification reporting for refunds."""

    @pytest.mark.asyncio
    async def test_report_verification_success(self, textverified_service):
        """Test successful verification reporting."""
        textverified_service.client.verifications.report.return_value = None

        result = await textverified_service.report_verification("ver123")

        assert result is True
        assert textverified_service.client.verifications.report.called

    @pytest.mark.asyncio
    async def test_report_verification_failure(self, textverified_service):
        """Test verification reporting when API fails."""
        textverified_service.client.verifications.report.side_effect = Exception(
            "API error"
        )

        result = await textverified_service.report_verification("ver123")

        assert result is False


class TestAreaCodeHandling:
    """Test area code preference and proximity logic."""

    @pytest.mark.asyncio
    async def test_build_area_code_preference(self, textverified_service):
        """Test building area code preference list."""
        mock_codes = [
            {"area_code": "202", "state": "DC"},
            {"area_code": "301", "state": "MD"},
            {"area_code": "703", "state": "VA"},
        ]

        with patch.object(
            textverified_service, "get_area_codes_list", return_value=mock_codes
        ):
            result = await textverified_service._build_area_code_preference("202")

        assert result[0] == "202"  # Requested code first
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_area_codes_list_from_cache(self, textverified_service):
        """Test area codes list retrieval from cache."""
        cached_codes = [{"area_code": "202", "state": "DC"}]

        with patch("app.core.unified_cache.cache.get", return_value=cached_codes):
            result = await textverified_service.get_area_codes_list()

        assert result == cached_codes


class TestReservations:
    """Test number reservation (rental) operations."""

    @pytest.mark.asyncio
    async def test_create_reservation_success(self, textverified_service):
        """Test successful reservation creation."""
        mock_reservation = Mock()
        mock_reservation.id = "res123"
        mock_reservation.number = "+12025551234"
        mock_reservation.total_cost = 10.0
        mock_reservation.ends_at = datetime.now(timezone.utc) + timedelta(hours=24)
        mock_reservation.state = Mock(value="active")

        textverified_service.client.reservations.create.return_value = mock_reservation

        result = await textverified_service.create_reservation(
            service="whatsapp", duration_hours=24.0
        )

        assert result["id"] == "res123"
        assert result["phone_number"] == "+12025551234"
        assert result["cost"] == 10.0

    @pytest.mark.asyncio
    async def test_get_reservation_messages(self, textverified_service, mock_sms):
        """Test retrieving messages for a reservation."""
        textverified_service.client.reservations.messages.return_value = [mock_sms]

        result = await textverified_service.get_reservation_messages("res123")

        assert len(result) == 1
        assert result[0]["code"] == "123456"


class TestHealthStatus:
    """Test service health status."""

    @pytest.mark.asyncio
    async def test_get_health_status_operational(self, textverified_service):
        """Test health status when service is operational."""
        textverified_service.client.account.balance = 100.0

        result = await textverified_service.get_health_status()

        assert result["status"] == "operational"
        assert result["enabled"] is True
        assert result["balance"] == 100.0

    @pytest.mark.asyncio
    async def test_get_health_status_disabled(self):
        """Test health status when service is disabled."""
        service = TextVerifiedService()
        service.enabled = False

        result = await service.get_health_status()

        assert result["status"] == "error"
        assert result["enabled"] is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_check_sms_with_error(self, textverified_service):
        """Test check_sms handles errors gracefully."""
        textverified_service.client.sms.list.side_effect = Exception("API error")

        result = await textverified_service.check_sms("ver123")

        # Service returns PENDING status on error, not ERROR
        assert result["status"] == "PENDING"
        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_get_verification_details_error(self, textverified_service):
        """Test get_verification_details handles errors gracefully."""
        textverified_service.client.verifications.details.side_effect = Exception(
            "API error"
        )

        result = await textverified_service.get_verification_details("ver123")

        assert result == {}


# Integration test markers
pytestmark = pytest.mark.unit
