"""Tests for v4.9.4 stability fixes:
- /api/notifications/categories 405 fix (double-prefix bug)
- Duplicate 'Still Waiting' notification prevention (Redis lock)
- Dark theme CSS hex fallbacks (static analysis)
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.notification import Notification
from app.models.user import User
from app.models.verification import Verification
from app.services.sms_polling_service import SMSPollingService


# ---------------------------------------------------------------------------
# Fix 1: /api/notifications/categories — no more 405
# ---------------------------------------------------------------------------


class TestNotificationCategoriesEndpoint:
    """Verify the double-prefix bug is fixed and the endpoint returns 200."""

    def test_categories_returns_200_not_405(self, authenticated_client, db, test_user):
        """GET /api/notifications/categories must return 200, not 405."""
        response = authenticated_client.get("/api/notifications/categories")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "Double-prefix bug may have returned."
        )

    def test_categories_response_shape(self, authenticated_client, db, test_user):
        """Response must contain a 'categories' list."""
        response = authenticated_client.get("/api/notifications/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_categories_with_notifications(self, authenticated_client, db, test_user):
        """Categories reflect actual notification types in the DB."""
        db.add(
            Notification(
                user_id=test_user.id,
                type="sms_received",
                title="SMS",
                message="code",
                is_read=False,
            )
        )
        db.add(
            Notification(
                user_id=test_user.id,
                type="payment_received",
                title="Payment",
                message="paid",
                is_read=True,
            )
        )
        db.commit()

        response = authenticated_client.get("/api/notifications/categories")
        assert response.status_code == 200
        types = {c["type"] for c in response.json()["categories"]}
        assert "sms_received" in types
        assert "payment_received" in types

    def test_categories_category_fields(self, authenticated_client, db, test_user):
        """Each category must have type, total, and unread fields."""
        db.add(
            Notification(
                user_id=test_user.id,
                type="verification_complete",
                title="Done",
                message="ok",
                is_read=False,
            )
        )
        db.commit()

        response = authenticated_client.get("/api/notifications/categories")
        assert response.status_code == 200
        for cat in response.json()["categories"]:
            assert "type" in cat
            assert "total" in cat
            assert "unread" in cat

    def test_categories_unread_count_accurate(self, authenticated_client, db, test_user):
        """Unread count must match actual unread notifications per type."""
        for is_read in [False, False, True]:
            db.add(
                Notification(
                    user_id=test_user.id,
                    type="balance_low",
                    title="Low",
                    message="low",
                    is_read=is_read,
                )
            )
        db.commit()

        response = authenticated_client.get("/api/notifications/categories")
        assert response.status_code == 200
        cats = {c["type"]: c for c in response.json()["categories"]}
        assert cats["balance_low"]["total"] == 3
        assert cats["balance_low"]["unread"] == 2

    def test_notification_center_endpoint_accessible(self, authenticated_client):
        """GET /api/notifications/center must also be reachable (not 405)."""
        response = authenticated_client.get("/api/notifications/center")
        assert response.status_code != 405


# ---------------------------------------------------------------------------
# Fix 2: Duplicate 'Still Waiting' notification — Redis lock
# ---------------------------------------------------------------------------


@pytest.fixture
def polling_service():
    svc = SMSPollingService()
    svc.textverified = AsyncMock()
    return svc


class TestNotifyWaitingDeduplication:
    """_notify_waiting must fire only once per verification across workers."""

    @pytest.mark.asyncio
    async def test_notify_waiting_accepts_verification_id(self, polling_service):
        """_notify_waiting signature must accept verification_id kwarg."""
        with patch("app.services.sms_polling_service.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_sl.return_value = mock_db
            mock_notif = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch(
                "app.services.sms_polling_service.NotificationService",
                return_value=mock_notif,
            ):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    # Must not raise TypeError for unexpected keyword argument
                    await polling_service._notify_waiting(
                        "user-1", "WhatsApp", verification_id="ver-1"
                    )

    @pytest.mark.asyncio
    async def test_second_worker_skipped_when_lock_held(self, polling_service):
        """When Redis lock is already held, second call must not create notification."""
        import fakeredis

        fake_redis = fakeredis.FakeRedis(decode_responses=True)

        # Pre-acquire the lock (simulates first worker)
        fake_redis.set("lock:notif_waiting:ver-42", "1", nx=True, ex=60)

        with patch("app.services.sms_polling_service.get_redis", return_value=fake_redis):
            with patch("app.services.sms_polling_service.SessionLocal") as mock_sl:
                mock_db = MagicMock()
                mock_sl.return_value = mock_db
                mock_notif = MagicMock()

                with patch(
                    "app.services.sms_polling_service.NotificationService",
                    return_value=mock_notif,
                ):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        await polling_service._notify_waiting(
                            "user-1", "WhatsApp", verification_id="ver-42"
                        )

                # Notification must NOT have been created
                mock_notif.create_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_first_worker_creates_notification(self, polling_service):
        """First worker to acquire lock must create the notification."""
        import fakeredis

        fake_redis = fakeredis.FakeRedis(decode_responses=True)

        with patch("app.services.sms_polling_service.get_redis", return_value=fake_redis):
            with patch("app.services.sms_polling_service.SessionLocal") as mock_sl:
                mock_db = MagicMock()
                mock_sl.return_value = mock_db
                mock_notif = MagicMock()

                with patch(
                    "app.services.sms_polling_service.NotificationService",
                    return_value=mock_notif,
                ):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        await polling_service._notify_waiting(
                            "user-1", "WhatsApp", verification_id="ver-99"
                        )

                mock_notif.create_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_key_is_per_verification(self, polling_service):
        """Different verification IDs must use different lock keys (no cross-blocking)."""
        import fakeredis

        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        # Lock ver-A
        fake_redis.set("lock:notif_waiting:ver-A", "1", nx=True, ex=60)

        with patch("app.services.sms_polling_service.get_redis", return_value=fake_redis):
            with patch("app.services.sms_polling_service.SessionLocal") as mock_sl:
                mock_db = MagicMock()
                mock_sl.return_value = mock_db
                mock_notif = MagicMock()

                with patch(
                    "app.services.sms_polling_service.NotificationService",
                    return_value=mock_notif,
                ):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        # ver-B is NOT locked — should proceed
                        await polling_service._notify_waiting(
                            "user-1", "WhatsApp", verification_id="ver-B"
                        )

                mock_notif.create_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_verification_id_still_works(self, polling_service):
        """Calling without verification_id (legacy) must not crash."""
        with patch("app.services.sms_polling_service.SessionLocal") as mock_sl:
            mock_db = MagicMock()
            mock_sl.return_value = mock_db
            mock_notif = MagicMock()

            with patch(
                "app.services.sms_polling_service.NotificationService",
                return_value=mock_notif,
            ):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    await polling_service._notify_waiting("user-1", "WhatsApp")

                mock_notif.create_notification.assert_called_once()


# ---------------------------------------------------------------------------
# Fix 3: Dark theme CSS hex fallbacks — static analysis
# ---------------------------------------------------------------------------


class TestDarkThemeCSSFallbacks:
    """Verify notification-improvements.css has explicit hex fallbacks."""

    @pytest.fixture(scope="class")
    def css_content(self):
        import os

        css_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "static",
            "css",
            "notification-improvements.css",
        )
        with open(css_path, encoding="utf-8") as f:
            return f.read()

    def test_dark_dropdown_has_hex_fallback(self, css_content):
        """[data-theme=dark] .notification-dropdown must have a hex background fallback."""
        assert "#1e293b" in css_content or "#1e2433" in css_content, (
            "Dark dropdown background must have explicit hex fallback"
        )

    def test_dark_dropdown_border_has_hex_fallback(self, css_content):
        """Dark dropdown border must have a hex fallback."""
        assert "#334155" in css_content, (
            "Dark dropdown border must have explicit hex fallback"
        )

    def test_dark_header_has_hex_fallback(self, css_content):
        """Dark dropdown header must have a hex background fallback."""
        assert "#0f172a" in css_content, (
            "Dark dropdown header must have explicit hex fallback"
        )

    def test_dark_notification_title_has_hex_fallback(self, css_content):
        """Dark notification title color must have a hex fallback."""
        assert "#f1f5f9" in css_content, (
            "Dark notification title must have explicit hex fallback"
        )

    def test_dark_notification_message_has_hex_fallback(self, css_content):
        """Dark notification message color must have a hex fallback."""
        assert "#cbd5e1" in css_content, (
            "Dark notification message must have explicit hex fallback"
        )

    def test_no_bare_gray800_var_in_dark_selectors(self, css_content):
        """All var(--gray-800) in dark selectors must have a fallback value."""
        import re

        # Find all var(--gray-NNN) without fallback inside [data-theme="dark"] blocks
        bare_vars = re.findall(r"var\(--gray-\d+\)(?!\s*,)", css_content)
        # Filter to only those inside dark selectors
        dark_section = css_content[css_content.find('[data-theme="dark"]'):]
        bare_in_dark = re.findall(r"var\(--gray-\d+\)(?!\s*,)", dark_section)
        assert len(bare_in_dark) == 0, (
            f"Found bare CSS vars without fallback in dark section: {bare_in_dark}"
        )
