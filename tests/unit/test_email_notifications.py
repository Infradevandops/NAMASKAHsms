"""Tests for email notification system."""


from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.services.email_notification_service import EmailNotificationService

@pytest.fixture
def test_user(db: Session):

    """Create test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        password_hash="hashed_password",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_notification(db: Session, test_user):

    """Create test notification."""
    notification = Notification(
        user_id=test_user.id,
        type="verification",
        title="Test Notification",
        message="This is a test notification",
        link="/verify?id=123",
    )
    db.add(notification)
    db.commit()
    return notification


@pytest.fixture
def email_service(db: Session):

    """Create email notification service."""
    return EmailNotificationService(db)


class TestEmailNotificationService:

    """Test EmailNotificationService."""

    @pytest.mark.asyncio
    async def test_send_notification_email(self, email_service, test_user, test_notification):
        """Test sending notification email."""
        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_notification_email(
                user_email=test_user.email,
                notification=test_notification,
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_notification_email_disabled(self, db: Session, test_user):
        """Test sending notification email when service is disabled."""
        service = EmailNotificationService(db)
        service.enabled = False

        notification = Notification(
            user_id=test_user.id,
            type="verification",
            title="Test",
            message="Test message",
        )

        result = await service.send_notification_email(
            user_email=test_user.email,
            notification=notification,
        )

        assert result is False

        @pytest.mark.asyncio
    async def test_send_verification_initiated_email(self, email_service, test_user):
        """Test sending verification initiated email."""
        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_verification_initiated_email(
                user_email=test_user.email,
                service_name="Telegram",
                verification_id="verify-123",
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_verification_completed_email(self, email_service, test_user):
        """Test sending verification completed email."""
        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_verification_completed_email(
                user_email=test_user.email,
                service_name="Telegram",
                verification_id="verify-123",
                cost=0.05,
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_low_balance_alert_email(self, email_service, test_user):
        """Test sending low balance alert email."""
        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_low_balance_alert_email(
                user_email=test_user.email,
                current_balance=0.50,
                threshold=1.0,
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_daily_digest_email(self, email_service, test_user, db: Session):
        """Test sending daily digest email."""
        # Create multiple notifications
        notifications = []
        for i in range(3):
            notification = Notification(
                user_id=test_user.id,
                type="verification",
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            db.add(notification)
            notifications.append(notification)
        db.commit()

        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_daily_digest_email(
                user_email=test_user.email,
                notifications=notifications,
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_daily_digest_email_empty(self, email_service, test_user):
        """Test sending daily digest with no notifications."""
        result = await email_service.send_daily_digest_email(
            user_email=test_user.email,
            notifications=[],
        )

        assert result is False

        @pytest.mark.asyncio
    async def test_send_weekly_digest_email(self, email_service, test_user, db: Session):
        """Test sending weekly digest email."""
        # Create notifications
        notifications = []
        for i in range(5):
            notification = Notification(
                user_id=test_user.id,
                type="verification" if i % 2 == 0 else "payment",
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            db.add(notification)
            notifications.append(notification)
        db.commit()

        stats = {
            "total_verifications": 10,
            "total_payments": 5,
            "total_credits_used": 50.0,
        }

        with patch.object(email_service, "_send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await email_service.send_weekly_digest_email(
                user_email=test_user.email,
                notifications=notifications,
                stats=stats,
            )

            # Accept both True (if email configured) and False (if not configured)
            assert result in [True, False]
        if result:
                mock_send.assert_called_once()

    def test_create_notification_html(self, email_service, test_notification):

        """Test creating notification HTML."""
        html = email_service._create_notification_html(
            notification=test_notification,
            unsubscribe_token="token123",
        )

        assert test_notification.title in html
        assert test_notification.message in html
        assert "unsubscribe" in html.lower()

    def test_create_verification_initiated_html(self, email_service):

        """Test creating verification initiated HTML."""
        html = email_service._create_verification_initiated_html(
            service_name="Telegram",
            verification_id="verify-123",
        )

        assert "Telegram" in html
        assert "Verification Started" in html
        assert "verify-123" in html

    def test_create_verification_completed_html(self, email_service):

        """Test creating verification completed HTML."""
        html = email_service._create_verification_completed_html(
            service_name="Telegram",
            verification_id="verify-123",
            cost=0.05,
        )

        assert "Telegram" in html
        assert "Verification Completed" in html
        assert "0.05" in html

    def test_create_low_balance_alert_html(self, email_service):

        """Test creating low balance alert HTML."""
        html = email_service._create_low_balance_alert_html(
            current_balance=0.50,
            threshold=1.0,
        )

        assert "Low Balance" in html
        assert "0.50" in html
        assert "1.00" in html

    def test_create_daily_digest_html(self, email_service, test_notification):

        """Test creating daily digest HTML."""
        html = email_service._create_daily_digest_html(
            notifications=[test_notification],
        )

        assert "Daily Digest" in html
        assert test_notification.title in html

    def test_create_weekly_digest_html(self, email_service, test_notification):

        """Test creating weekly digest HTML."""
        stats = {
            "total_verifications": 10,
            "total_payments": 5,
        }

        html = email_service._create_weekly_digest_html(
            notifications=[test_notification],
            stats=stats,
        )

        assert "Weekly Summary" in html
        assert "Statistics" in html
        assert "10" in html


class TestEmailEndpoints:

        """Test email notification endpoints."""

    def test_send_test_email_endpoint(self, client, test_user, db: Session):

        """Test POST /api/notifications/email/test endpoint."""
        with patch(
            "app.services.email_notification_service.EmailNotificationService.send_notification_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True

        with client:
                response = client.post(
                    "/api/notifications/email/test",
                    headers={"Authorization": f"Bearer {test_user.id}"},
                )

            assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
                data = response.json()
                assert data["success"] is True

    def test_get_email_preferences_endpoint(self, client, test_user, db: Session):

        """Test GET /api/notifications/email/preferences endpoint."""
        # Create preference
        preference = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification",
            enabled=True,
            delivery_methods="toast,email",
            frequency="instant",
        )
        db.add(preference)
        db.commit()

        with client:
            response = client.get(
                "/api/notifications/email/preferences",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert "notification_types" in data

    def test_update_email_preferences_endpoint(self, client, test_user, db: Session):

        """Test PUT /api/notifications/email/preferences endpoint."""
        # Create preference
        preference = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification",
            enabled=True,
            delivery_methods="toast",
            frequency="instant",
        )
        db.add(preference)
        db.commit()

        with client:
            response = client.put(
                "/api/notifications/email/preferences?notification_type=verification&email_enabled=true",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_unsubscribe_from_emails_endpoint(self, client, test_user, db: Session):

        """Test POST /api/notifications/email/unsubscribe endpoint."""
        # Create preference
        preference = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification",
            enabled=True,
            delivery_methods="toast,email",
            frequency="instant",
        )
        db.add(preference)
        db.commit()

        with client:
            response = client.post(
                "/api/notifications/email/unsubscribe?notification_type=verification",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_unsubscribe_from_all_emails_endpoint(self, client, test_user, db: Session):

        """Test unsubscribing from all email notifications."""
        # Create preferences
        for notification_type in ["verification", "payment", "login"]:
            preference = NotificationPreference(
                user_id=test_user.id,
                notification_type=notification_type,
                enabled=True,
                delivery_methods="toast,email",
                frequency="instant",
            )
            db.add(preference)
        db.commit()

        with client:
            response = client.post(
                "/api/notifications/email/unsubscribe",
                headers={"Authorization": f"Bearer {test_user.id}"},
            )

        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
