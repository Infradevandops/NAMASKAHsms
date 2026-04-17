"""
Unit tests for Notification Enhancements (Phase 6 - Notifications)
Tests retry notifications and area code fallback alerts
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.notification_dispatcher import NotificationDispatcher


class TestRetryNotifications:
    """Test retry attempt notifications"""

    @pytest.mark.asyncio
    async def test_notify_retry_attempt_called(self):
        """Test retry notification is sent when retry occurs"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_retry_attempt(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                attempt=1,
                max_attempts=3,
                reason="area_code_mismatch",
            )

            assert mock_create.called
            call_args = mock_create.call_args[1]
            assert call_args["user_id"] == "user_123"
            assert call_args["notification_type"] == "verification_retry"
            assert "Retry 1/3" in call_args["title"]

    @pytest.mark.asyncio
    async def test_retry_notification_includes_reason(self):
        """Test retry notification includes mismatch reason"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_retry_attempt(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                attempt=2,
                max_attempts=3,
                reason="carrier_mismatch",
            )

            call_args = mock_create.call_args[1]
            assert "carrier" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_retry_notification_final_attempt(self):
        """Test retry notification for final attempt"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_retry_attempt(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                attempt=3,
                max_attempts=3,
                reason="voip_detected",
            )

            call_args = mock_create.call_args[1]
            assert (
                "final" in call_args["message"].lower()
                or "final" in call_args["title"].lower()
            )


class TestAreaCodeFallbackNotifications:
    """Test area code fallback notifications"""

    @pytest.mark.asyncio
    async def test_notify_same_state_fallback(self):
        """Test notification for same-state area code fallback"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_area_code_fallback(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                requested_area_code="415",
                assigned_area_code="510",
                same_state=True,
            )

            assert mock_create.called
            call_args = mock_create.call_args[1]
            assert call_args["notification_type"] == "area_code_fallback"
            assert "same state" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_notify_cross_state_fallback(self):
        """Test notification for cross-state area code fallback"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_area_code_fallback(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                requested_area_code="415",
                assigned_area_code="212",
                same_state=False,
            )

            call_args = mock_create.call_args[1]
            assert "different state" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_fallback_notification_includes_area_codes(self):
        """Test fallback notification includes both area codes"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        with patch.object(
            dispatcher.notification_service, "create_notification"
        ) as mock_create:
            mock_create.return_value = Mock(to_dict=lambda: {"title": "test"})

            await dispatcher.notify_area_code_fallback(
                user_id="user_123",
                verification_id="ver_123",
                service="whatsapp",
                requested_area_code="415",
                assigned_area_code="510",
                same_state=True,
            )

            call_args = mock_create.call_args[1]
            message = call_args["message"]
            assert "415" in message
            assert "510" in message


class TestNotificationIntegration:
    """Test notification integration with existing system"""

    @pytest.mark.asyncio
    async def test_notifications_dont_block_purchase(self):
        """Test notification failures don't block verification purchase"""
        db = Mock()
        dispatcher = NotificationDispatcher(db)

        # Simulate notification failure
        with patch.object(
            dispatcher.notification_service,
            "create_notification",
            side_effect=Exception("DB error"),
        ):
            # Should not raise exception
            try:
                await dispatcher.notify_retry_attempt(
                    user_id="user_123",
                    verification_id="ver_123",
                    service="whatsapp",
                    attempt=1,
                    max_attempts=3,
                    reason="area_code_mismatch",
                )
                # Success - exception was caught
            except Exception:
                pytest.fail("Notification failure should not raise exception")
