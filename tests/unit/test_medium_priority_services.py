"""Unit tests for medium-priority services — Issues 10-14 from STABILITY_CHECKLIST.md."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Issue 10: SMS Gateway
# ═══════════════════════════════════════════════════════════════════════════════


class TestSMSGateway:
    @pytest.fixture
    def gateway(self):
        from app.services.sms_gateway import SMSGateway

        return SMSGateway(provider="twilio")

    @pytest.fixture
    def webhook_gateway(self):
        from app.services.sms_gateway import SMSGateway

        return SMSGateway(provider="webhook")

    @pytest.mark.asyncio
    async def test_send_sms_twilio_success(self, gateway):
        result = await gateway.send_sms("+12025551234", "Your code is 123456")
        assert result["status"] == "sent"
        assert result["provider"] == "twilio"

    @pytest.mark.asyncio
    async def test_send_sms_manual_fallback(self):
        from app.services.sms_gateway import SMSGateway

        gw = SMSGateway(provider="unknown")
        result = await gw.send_sms("+12025551234", "test")
        assert result["status"] == "manual"

    @pytest.mark.asyncio
    async def test_send_sms_webhook_success(self, webhook_gateway):
        import httpx

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value = mock_client

            result = await webhook_gateway.send_sms("+12025551234", "test")

        assert result["status"] == "sent"
        assert result["provider"] == "webhook"

    @pytest.mark.asyncio
    async def test_receive_sms_returns_list(self, gateway):
        result = await gateway.receive_sms("+12025551234")
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════════════
# Issue 11: Adaptive Polling
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdaptivePolling:
    @pytest.fixture
    def service(self):
        from app.services.adaptive_polling import AdaptivePollingService

        return AdaptivePollingService()

    def _make_db(self, verifications):
        db = MagicMock()
        db.query.return_value.filter.return_value = db.query.return_value
        db.query.return_value.filter.return_value.filter.return_value = (
            db.query.return_value
        )
        db.query.return_value.all.return_value = verifications
        return db

    def _make_verification(self, status="completed", seconds_to_complete=30):
        v = MagicMock()
        v.status = status
        v.service_name = "whatsapp"
        now = datetime.now(timezone.utc)
        v.created_at = now - timedelta(seconds=seconds_to_complete)
        v.completed_at = now if status == "completed" else None
        return v

    def test_get_optimal_interval_no_data(self, service):
        db = self._make_db([])
        with patch("app.services.adaptive_polling.settings") as mock_settings:
            mock_settings.sms_polling_initial_interval_seconds = 5.0
            result = service.get_optimal_interval(db)
        assert result == 5.0

    def test_get_optimal_interval_fast_completions(self, service):
        verifications = [
            self._make_verification(seconds_to_complete=15) for _ in range(5)
        ]
        db = self._make_db(verifications)
        result = service.get_optimal_interval(db)
        assert 5 <= result <= 30

    def test_get_optimal_interval_slow_completions(self, service):
        verifications = [
            self._make_verification(seconds_to_complete=90) for _ in range(5)
        ]
        db = self._make_db(verifications)
        result = service.get_optimal_interval(db)
        assert 5 <= result <= 30

    def test_should_increase_interval_low_success(self, service):
        verifications = [self._make_verification(status="completed")] * 3 + [
            self._make_verification(status="timeout")
        ] * 7
        db = self._make_db(verifications)
        assert service.should_increase_interval(db) is True

    def test_should_increase_interval_high_success(self, service):
        verifications = [self._make_verification(status="completed")] * 10
        db = self._make_db(verifications)
        assert service.should_increase_interval(db) is False

    def test_should_increase_interval_insufficient_data(self, service):
        verifications = [self._make_verification(status="timeout")] * 3
        db = self._make_db(verifications)
        assert service.should_increase_interval(db) is False

    def test_should_decrease_interval_high_success(self, service):
        verifications = [self._make_verification(status="completed")] * 10
        db = self._make_db(verifications)
        assert service.should_decrease_interval(db) is True

    def test_should_decrease_interval_low_success(self, service):
        verifications = [self._make_verification(status="completed")] * 5 + [
            self._make_verification(status="timeout")
        ] * 5
        db = self._make_db(verifications)
        assert service.should_decrease_interval(db) is False

    def test_get_service_specific_interval_returns_int(self, service):
        db = self._make_db([])
        with patch("app.services.adaptive_polling.settings") as mock_settings:
            mock_settings.sms_polling_initial_interval_seconds = 5.0
            result = service.get_service_specific_interval(db, "whatsapp")
        assert isinstance(result, int)
        assert 5 <= result <= 30


# ═══════════════════════════════════════════════════════════════════════════════
# Issue 12: Availability Service
# ═══════════════════════════════════════════════════════════════════════════════


class TestAvailabilityService:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        from app.services.availability_service import AvailabilityService

        return AvailabilityService(db)

    def _make_verifications(self, completed=8, total=10):
        verifications = []
        now = datetime.now(timezone.utc)
        for i in range(total):
            v = MagicMock()
            v.status = "completed" if i < completed else "timeout"
            v.created_at = now - timedelta(minutes=30)
            v.completed_at = (
                now - timedelta(minutes=25) if v.status == "completed" else None
            )
            verifications.append(v)
        return verifications

    def test_get_service_availability_excellent(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = self._make_verifications(
            completed=10, total=10
        )
        result = service.get_service_availability("whatsapp")
        assert result["status"] == "excellent"
        assert result["success_rate"] == 100.0

    def test_get_service_availability_poor(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = self._make_verifications(
            completed=2, total=10
        )
        result = service.get_service_availability("whatsapp")
        assert result["status"] == "poor"

    def test_get_service_availability_no_data(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
            []
        )
        result = service.get_service_availability("whatsapp")
        assert result["status"] == "unknown"
        assert result["total_attempts"] == 0

    def test_get_country_availability(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = self._make_verifications(
            completed=9, total=10
        )
        result = service.get_country_availability("US")
        assert result["success_rate"] == 90.0
        assert result["status"] == "excellent"

    def test_get_carrier_availability_no_data(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
            []
        )
        result = service.get_carrier_availability("verizon")
        assert result["status"] == "unknown"

    def test_get_area_code_availability(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = self._make_verifications(
            completed=8, total=10
        )
        result = service.get_area_code_availability("415")
        assert result["success_rate"] == 80.0

    def test_get_availability_summary(self, service, db):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = self._make_verifications(
            completed=9, total=10
        )
        result = service.get_availability_summary("whatsapp", "US")
        assert "service" in result
        assert "country" in result
        assert "overall" in result
        assert result["overall"]["recommendation"] in (
            "excellent",
            "good",
            "fair",
            "poor",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Issue 13: Business Intelligence
# ═══════════════════════════════════════════════════════════════════════════════


class TestBusinessIntelligence:
    @pytest.fixture
    def service(self):
        from app.services.business_intelligence import BusinessIntelligenceService

        db = MagicMock()
        return BusinessIntelligenceService(db)

    def test_service_instantiates(self):
        from app.services.business_intelligence import BusinessIntelligenceService

        db = MagicMock()
        svc = BusinessIntelligenceService(db)
        assert svc is not None

    def test_has_db_attribute(self, service):
        assert hasattr(service, "db")


# ═══════════════════════════════════════════════════════════════════════════════
# Issue 14: Event Broadcaster
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventBroadcaster:
    @pytest.fixture
    def broadcaster(self):
        from app.services.event_broadcaster import EventBroadcaster

        return EventBroadcaster()

    @pytest.mark.asyncio
    async def test_broadcast_notification_success(self, broadcaster):
        notification = MagicMock()
        notification.id = "notif-1"
        notification.type = "info"
        notification.title = "Test"
        notification.message = "Hello"
        notification.link = None
        notification.icon = None

        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(return_value=True)
            result = await broadcaster.broadcast_notification("user-1", notification)

        assert result is True

    @pytest.mark.asyncio
    async def test_broadcast_notification_user_not_connected(self, broadcaster):
        notification = MagicMock()
        notification.id = "notif-1"
        notification.type = "info"
        notification.title = "Test"
        notification.message = "Hello"
        notification.link = None
        notification.icon = None

        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(return_value=False)
            result = await broadcaster.broadcast_notification("user-1", notification)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_notification_error_returns_false(self, broadcaster):
        notification = MagicMock()

        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(side_effect=Exception("WS error"))
            result = await broadcaster.broadcast_notification("user-1", notification)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_activity_success(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(return_value=True)
            result = await broadcaster.broadcast_activity(
                "user-1", "verification", "Verification started"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_broadcast_payment_event(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(return_value=True)
            result = await broadcaster.broadcast_payment_event(
                "user-1", "completed", 10.0, "ref-123", "success"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_broadcast_verification_event(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_user = AsyncMock(return_value=True)
            result = await broadcaster.broadcast_verification_event(
                "user-1", "completed", "whatsapp", "verif-1", "completed"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_broadcast_to_channel_returns_count(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_channel = AsyncMock(return_value=5)
            result = await broadcaster.broadcast_to_channel(
                "notifications", "info", "Title", "Content"
            )
        assert result == 5

    @pytest.mark.asyncio
    async def test_broadcast_to_channel_error_returns_zero(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.broadcast_to_channel = AsyncMock(side_effect=Exception("WS error"))
            result = await broadcaster.broadcast_to_channel(
                "notifications", "info", "Title", "Content"
            )
        assert result == 0

    def test_get_connection_stats(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.get_active_connections_count.return_value = 10
            mock_mgr.get_active_users.return_value = ["user-1", "user-2"]
            stats = broadcaster.get_connection_stats()

        assert stats["active_connections"] == 10
        assert stats["active_users"] == 2

    def test_get_connection_stats_error_returns_zeros(self, broadcaster):
        with patch("app.services.event_broadcaster.connection_manager") as mock_mgr:
            mock_mgr.get_active_connections_count.side_effect = Exception("error")
            stats = broadcaster.get_connection_stats()

        assert stats["active_connections"] == 0
        assert stats["active_users"] == 0
