"""Unit tests for service classes."""
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import AuthenticationError, ValidationError
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService


class TestAuthService:
    """Test authentication service."""

    def test_register_user(self, db_session):
        """Test user registration."""
        auth_service = AuthService(db_session)

        user = auth_service.register_user(
            email="newuser@example.com",
            password="password123"
        )

        assert user.email == "newuser@example.com"
        assert user.credits == 0.0
        assert user.free_verifications == 1.0
        assert not user.is_admin

    def test_authenticate_user_success(self, db_session, test_user):
        """Test successful authentication."""
        auth_service = AuthService(db_session)

        user = auth_service.authenticate_user(
            email="test@example.com",
            password="testpass123"
        )

        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_authenticate_user_invalid_password(self, db_session, test_user):
        """Test authentication with invalid password."""
        auth_service = AuthService(db_session)

        with pytest.raises(AuthenticationError):
            auth_service.authenticate_user(
                email="test@example.com",
                password="wrongpassword"
            )

    def test_create_access_token(self, db_session):
        """Test JWT token creation."""
        auth_service = AuthService(db_session)

        token = auth_service.create_access_token("user_123")

        assert isinstance(token, str)
        assert len(token) > 0


class TestPaymentService:
    """Test payment service."""

    @patch('httpx.AsyncClient.post')
    async def test_initialize_payment(self, mock_post, db_session):
        """Test payment initialization."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "authorization_url": "https://checkout.paystack.com/test",
                "access_code": "test_access_code"
            }
        }
        mock_post.return_value = mock_response

        payment_service = PaymentService(db_session)

        result = await payment_service.initialize_payment(
            user_id="user_123",
            email="test@example.com",
            amount_usd=10.0
        )

        assert result["success"] is True
        assert "authorization_url" in result
        assert "access_code" in result

    def test_verify_webhook_signature(self, db_session):
        """Test webhook signature verification."""
        payment_service = PaymentService(db_session)
        payment_service.secret_key = "test_secret"

        payload = b'{"event": "charge.success"}'

        # Generate valid signature
        import hashlib
        import hmac
        signature = hmac.new(
            b"test_secret",
            payload,
            hashlib.sha512
        ).hexdigest()

        assert payment_service.verify_webhook_signature(payload, signature) is True
        assert payment_service.verify_webhook_signature(payload, "invalid") is False


class TestNotificationService:
    """Test notification service."""

    def test_create_in_app_notification(self, db_session):
        """Test in-app notification creation."""
        notification_service = NotificationService(db_session)

        notification = notification_service.create_in_app_notification(
            user_id="user_123",
            title="Test Notification",
            message="This is a test message",
            notification_type="info"
        )

        assert notification.user_id == "user_123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.type == "info"
        assert not notification.is_read

    def test_get_user_notifications(self, db_session):
        """Test getting user notifications."""
        notification_service = NotificationService(db_session)

        # Create test notifications
        notification_service.create_in_app_notification(
            user_id="user_123",
            title="Notification 1",
            message="Message 1"
        )
        notification_service.create_in_app_notification(
            user_id="user_123",
            title="Notification 2",
            message="Message 2"
        )

        notifications = notification_service.get_user_notifications("user_123")

        assert len(notifications) == 2
        assert notifications[0]["title"] == "Notification 2"  # Most recent first

    def test_mark_notification_read(self, db_session):
        """Test marking notification as read."""
        notification_service = NotificationService(db_session)

        notification = notification_service.create_in_app_notification(
            user_id="user_123",
            title="Test",
            message="Test message"
        )

        success = notification_service.mark_notification_read(
            notification.id, "user_123"
        )

        assert success is True

        # Verify notification is marked as read
        notifications = notification_service.get_user_notifications("user_123")
        assert notifications[0]["is_read"] is True
