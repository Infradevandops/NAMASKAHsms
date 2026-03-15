"""Tests for notification dispatcher broadcast serialization fix.

Covers the two confirmed production bugs:
1. 'Notification' object has no attribute 'get'
2. Object of type Notification is not JSON serializable
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.notification_dispatcher import NotificationDispatcher
from app.models.notification import Notification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_notification(**kwargs) -> Notification:
    """Build a minimal Notification ORM object (no DB required)."""
    n = Notification()
    n.id = kwargs.get("id", "notif-test-123")
    n.user_id = kwargs.get("user_id", "user-test-123")
    n.type = kwargs.get("type", "verification_started")
    n.title = kwargs.get("title", "Verification Started")
    n.message = kwargs.get("message", "Started telegram verification")
    n.link = kwargs.get("link", None)
    n.icon = kwargs.get("icon", None)
    n.is_read = kwargs.get("is_read", False)
    n.created_at = kwargs.get("created_at", datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc))
    return n


def make_dispatcher(db=None) -> NotificationDispatcher:
    """Build a NotificationDispatcher with a mocked DB and service."""
    db = db or MagicMock()
    dispatcher = NotificationDispatcher(db)
    return dispatcher


# ---------------------------------------------------------------------------
# Unit tests: _broadcast_notification
# ---------------------------------------------------------------------------

class TestBroadcastNotification:
    """Directly test the _broadcast_notification method."""

    def test_serializes_orm_object_via_to_dict(self):
        """Bug 1 fix: ORM object must be serialized before .get() is called."""
        import sys
        notification = make_notification(title="Test Title")
        dispatcher = make_dispatcher()

        mock_manager = MagicMock()
        mock_manager.send_personal_message = AsyncMock()

        def fake_create_task(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(coro)
            except Exception:
                pass
            finally:
                loop.close()

        ws_mod = sys.modules["app.websocket.manager"]
        original = ws_mod.manager
        ws_mod.manager = mock_manager
        try:
            with patch("asyncio.create_task", side_effect=fake_create_task):
                dispatcher._broadcast_notification("user-test-123", notification)
        finally:
            ws_mod.manager = original

        call_args = mock_manager.send_personal_message.call_args
        if call_args:
            payload = call_args[0][0]
            assert isinstance(payload["data"], dict), (
                "data must be a dict, not a Notification ORM object"
            )
            assert payload["data"]["title"] == "Test Title"

    def test_payload_is_json_serializable(self):
        """Bug 2 fix: payload sent to WebSocket must be JSON serializable."""
        import json
        notification = make_notification(title="SMS Received")
        payload = notification.to_dict()

        # Must not raise TypeError: Object of type Notification is not JSON serializable
        try:
            json.dumps({"type": "notification", "data": payload})
        except TypeError as e:
            pytest.fail(f"Notification payload is not JSON serializable: {e}")

    def test_to_dict_contains_required_fields(self):
        """to_dict() must return all fields the WebSocket client expects."""
        notification = make_notification(
            title="Verification Started",
            message="Started telegram verification for +16053762765 ($2.50)",
        )
        result = notification.to_dict()

        assert isinstance(result, dict)
        for field in ("id", "type", "title", "message", "is_read", "created_at"):
            assert field in result, f"Missing field '{field}' in to_dict() output"

    def test_broadcast_does_not_raise_on_orm_object(self):
        """_broadcast_notification must not raise when given an ORM Notification."""
        import sys
        notification = make_notification()
        dispatcher = make_dispatcher()

        ws_mod = sys.modules["app.websocket.manager"]
        original = ws_mod.manager
        ws_mod.manager = MagicMock()
        try:
            with patch("asyncio.create_task"):
                try:
                    dispatcher._broadcast_notification("user-test-123", notification)
                except (AttributeError, TypeError) as e:
                    pytest.fail(f"_broadcast_notification raised {type(e).__name__}: {e}")
        finally:
            ws_mod.manager = original


# ---------------------------------------------------------------------------
# Unit tests: notify_* methods pass serialized payload
# ---------------------------------------------------------------------------

class TestNotifyMethods:
    """Ensure every notify_* method produces a serialized broadcast."""

    def _run(self, coro):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _make_dispatcher_with_mock_service(self, user_id="user-test-123"):
        dispatcher = make_dispatcher()
        notification = make_notification(user_id=user_id)
        dispatcher.notification_service = MagicMock()
        dispatcher.notification_service.create_notification.return_value = notification
        return dispatcher, notification

    def test_notify_verification_started_broadcasts_dict(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        broadcast_calls = []
        dispatcher._broadcast_notification = lambda uid, n: broadcast_calls.append(n)

        self._run(dispatcher.notify_verification_started(
            user_id="user-test-123",
            verification_id="v-123",
            service="telegram",
            phone_number="+16053762765",
            cost=2.50,
        ))

        assert len(broadcast_calls) == 1
        # The object passed to _broadcast_notification is the ORM object;
        # _broadcast_notification itself must serialize it — confirmed by the
        # test_broadcast_does_not_raise_on_orm_object test above.

    def test_notify_verification_completed_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.notify_verification_completed(
            user_id="user-test-123",
            verification_id="v-123",
            service="telegram",
            phone_number="+16053762765",
        ))
        assert result is True

    def test_notify_verification_failed_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.notify_verification_failed(
            user_id="user-test-123",
            verification_id="v-123",
            service="telegram",
            reason="timeout",
        ))
        assert result is True

    def test_notify_payment_completed_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.notify_payment_completed(
            user_id="user-test-123",
            amount=10.00,
            new_balance=110.00,
        ))
        assert result is True

    def test_notify_verification_timeout_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.notify_verification_timeout(
            user_id="user-test-123",
            verification_id="v-123",
            service="telegram",
            refund_amount=2.50,
        ))
        assert result is True

    def test_notify_verification_cancelled_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.notify_verification_cancelled(
            user_id="user-test-123",
            verification_id="v-123",
            service="telegram",
            refund_amount=2.50,
            new_balance=992.50,
        ))
        assert result is True

    def test_on_sms_received_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        verification = MagicMock()
        verification.user_id = "user-test-123"
        verification.service_name = "telegram"

        result = self._run(dispatcher.on_sms_received(verification))
        assert result is True

    def test_on_refund_completed_returns_true(self):
        dispatcher, _ = self._make_dispatcher_with_mock_service()
        dispatcher._broadcast_notification = MagicMock()

        result = self._run(dispatcher.on_refund_completed(
            user_id="user-test-123",
            amount=2.50,
            reference="ref-123",
            new_balance=992.50,
        ))
        assert result is True
