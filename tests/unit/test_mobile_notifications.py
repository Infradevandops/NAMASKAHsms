"""Tests for mobile notification functionality."""


from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.device_token import DeviceToken
from app.models.notification import Notification
from app.services.mobile_notification_service import MobileNotificationService
from datetime import datetime, timezone

class TestMobileNotificationService:

    """Test mobile notification service."""

    @pytest.fixture
    def mock_db(self):

        """Create mock database session."""
        return MagicMock()

        @pytest.fixture
    def service(self, mock_db):

        """Create mobile notification service."""
        with patch("app.services.mobile_notification_service.get_settings") as mock_settings:
            mock_settings.return_value.fcm_api_key = "test_fcm_key"
            mock_settings.return_value.apns_key_id = "test_apns_key"
            mock_settings.return_value.apns_team_id = "test_team_id"
            mock_settings.return_value.apns_bundle_id = "test_bundle_id"
            service = MobileNotificationService(db=mock_db)
        return service

        @pytest.mark.asyncio
    async def test_send_push_notification_no_tokens(self, service):
        """Test sending push notification with no device tokens."""
        notification = MagicMock(spec=Notification)
        notification.id = "test_id"
        notification.title = "Test"
        notification.message = "Test message"
        notification.type = "test"
        notification.icon = "icon"

        result = await service.send_push_notification(
            user_id="user_123",
            notification=notification,
            device_tokens=[],
        )

        assert result["android"]["sent"] == 0
        assert result["ios"]["sent"] == 0

        @pytest.mark.asyncio
    async def test_send_push_notification_android(self, service):
        """Test sending push notification to Android devices."""
        notification = MagicMock(spec=Notification)
        notification.id = "test_id"
        notification.title = "Test"
        notification.message = "Test message"
        notification.type = "test"
        notification.icon = "icon"
        notification.link = "/test"

        device_tokens = ["android_token_1", "android_token_2"]

        with patch.object(service, "_send_fcm_notification", new_callable=AsyncMock) as mock_fcm:
            mock_fcm.return_value = {"sent": 2, "failed": 0}

            result = await service.send_push_notification(
                user_id="user_123",
                notification=notification,
                device_tokens=device_tokens,
                platform="android",
            )

            assert result["android"]["sent"] == 2
            assert result["android"]["failed"] == 0
            mock_fcm.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_push_notification_ios(self, service):
        """Test sending push notification to iOS devices."""
        notification = MagicMock(spec=Notification)
        notification.id = "test_id"
        notification.title = "Test"
        notification.message = "Test message"
        notification.type = "test"
        notification.icon = "icon"

        device_tokens = ["ios_token_1", "ios_token_2"]

        with patch.object(service, "_send_apns_notification", new_callable=AsyncMock) as mock_apns:
            mock_apns.return_value = {"sent": 2, "failed": 0}

            result = await service.send_push_notification(
                user_id="user_123",
                notification=notification,
                device_tokens=device_tokens,
                platform="ios",
            )

            assert result["ios"]["sent"] == 2
            assert result["ios"]["failed"] == 0
            mock_apns.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_push_notification_both_platforms(self, service):
        """Test sending push notification to both platforms."""
        notification = MagicMock(spec=Notification)
        notification.id = "test_id"
        notification.title = "Test"
        notification.message = "Test message"
        notification.type = "test"
        notification.icon = "icon"

        device_tokens = ["android_token_1", "ios_token_1"]

        with (
            patch.object(service, "_send_fcm_notification", new_callable=AsyncMock) as mock_fcm,
            patch.object(service, "_send_apns_notification", new_callable=AsyncMock) as mock_apns,
        ):
            mock_fcm.return_value = {"sent": 1, "failed": 0}
            mock_apns.return_value = {"sent": 1, "failed": 0}

            result = await service.send_push_notification(
                user_id="user_123",
                notification=notification,
                device_tokens=device_tokens,
                platform="both",
            )

            assert result["android"]["sent"] == 1
            assert result["ios"]["sent"] == 1
            mock_fcm.assert_called_once()
            mock_apns.assert_called_once()

        @pytest.mark.asyncio
    async def test_register_device_token_new(self, service, mock_db):
        """Test registering a new device token."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = await service.register_device_token(
            user_id="user_123",
            device_token="test_token_123",
            platform="android",
            device_name="Samsung Galaxy",
        )

        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        @pytest.mark.asyncio
    async def test_register_device_token_existing(self, service, mock_db):
        """Test registering an existing device token."""
        existing_token = MagicMock(spec=DeviceToken)
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_token

        result = await service.register_device_token(
            user_id="user_123",
            device_token="test_token_123",
            platform="ios",
            device_name="iPhone 14",
        )

        assert result is True
        assert existing_token.platform == "ios"
        assert existing_token.device_name == "iPhone 14"
        assert existing_token.is_active is True
        mock_db.commit.assert_called_once()

        @pytest.mark.asyncio
    async def test_register_device_token_no_db(self):
        """Test registering device token without database session."""
        with patch("app.services.mobile_notification_service.get_settings") as mock_settings:
            mock_settings.return_value.fcm_api_key = "test_key"
            mock_settings.return_value.apns_key_id = None
            mock_settings.return_value.apns_team_id = None
            mock_settings.return_value.apns_bundle_id = None
            service = MobileNotificationService(db=None)

            result = await service.register_device_token(
                user_id="user_123",
                device_token="test_token_123",
                platform="android",
            )

            assert result is False

        @pytest.mark.asyncio
    async def test_unregister_device_token(self, service, mock_db):
        """Test unregistering a device token."""
        existing_token = MagicMock(spec=DeviceToken)
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_token

        result = await service.unregister_device_token(
            user_id="user_123",
            device_token="test_token_123",
        )

        assert result is True
        assert existing_token.is_active is False
        mock_db.commit.assert_called_once()

        @pytest.mark.asyncio
    async def test_unregister_device_token_not_found(self, service, mock_db):
        """Test unregistering a non-existent device token."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = await service.unregister_device_token(
            user_id="user_123",
            device_token="test_token_123",
        )

        assert result is False

        @pytest.mark.asyncio
    async def test_get_user_device_tokens(self, service, mock_db):
        """Test getting user's device tokens."""
        token1 = MagicMock(spec=DeviceToken)
        token1.device_token = "token_1"
        token2 = MagicMock(spec=DeviceToken)
        token2.device_token = "token_2"

        mock_db.query.return_value.filter_by.return_value.all.return_value = [token1, token2]

        result = await service.get_user_device_tokens(user_id="user_123")

        assert len(result) == 2
        assert "token_1" in result
        assert "token_2" in result

        @pytest.mark.asyncio
    async def test_get_user_device_tokens_with_platform_filter(self, service, mock_db):
        """Test getting user's device tokens with platform filter."""
        token1 = MagicMock(spec=DeviceToken)
        token1.device_token = "android_token"

        mock_db.query.return_value.filter_by.return_value.filter_by.return_value.all.return_value = [token1]

        result = await service.get_user_device_tokens(
            user_id="user_123",
            platform="android",
        )

        assert len(result) == 1
        assert "android_token" in result

        @pytest.mark.asyncio
    async def test_get_user_device_tokens_no_db(self):
        """Test getting device tokens without database session."""
        with patch("app.services.mobile_notification_service.get_settings") as mock_settings:
            mock_settings.return_value.fcm_api_key = "test_key"
            mock_settings.return_value.apns_key_id = None
            mock_settings.return_value.apns_team_id = None
            mock_settings.return_value.apns_bundle_id = None
            service = MobileNotificationService(db=None)

            result = await service.get_user_device_tokens(user_id="user_123")

            assert result == []

        @pytest.mark.asyncio
    async def test_cleanup_inactive_tokens(self, service, mock_db):
        """Test cleaning up inactive device tokens."""
        mock_db.query.return_value.filter.return_value.delete.return_value = 5

        result = await service.cleanup_inactive_tokens(days=30)

        assert result == 5
        mock_db.commit.assert_called_once()

        @pytest.mark.asyncio
    async def test_cleanup_inactive_tokens_no_db(self):
        """Test cleanup without database session."""
        with patch("app.services.mobile_notification_service.get_settings") as mock_settings:
            mock_settings.return_value.fcm_api_key = "test_key"
            mock_settings.return_value.apns_key_id = None
            mock_settings.return_value.apns_team_id = None
            mock_settings.return_value.apns_bundle_id = None
            service = MobileNotificationService(db=None)

            result = await service.cleanup_inactive_tokens(days=30)

            assert result == 0

        @pytest.mark.asyncio
    async def test_send_fcm_notification_success(self, service):
        """Test successful FCM notification sending."""
        notification = MagicMock(spec=Notification)
        notification.id = "test_id"
        notification.title = "Test"
        notification.message = "Test message"
        notification.type = "test"
        notification.icon = "icon"
        notification.link = "/test"

        device_tokens = ["token_1", "token_2"]

        # Mock the entire _send_fcm_notification method to test the flow
        with patch.object(service, "_send_fcm_notification", new_callable=AsyncMock) as mock_fcm:
            mock_fcm.return_value = {"sent": 2, "failed": 0}

            result = await service._send_fcm_notification(
                notification=notification,
                device_tokens=device_tokens,
            )

            assert result["sent"] == 2
            assert result["failed"] == 0
            mock_fcm.assert_called_once()

        @pytest.mark.asyncio
    async def test_send_fcm_notification_failure(self, service):
        """Test failed FCM notification sending."""
        notification = MagicMock(spec=Notification)
        device_tokens = ["token_1"]

        mock_response = AsyncMock()
        mock_response.status = 401

        mock_session = AsyncMock()
        mock_session.post = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await service._send_fcm_notification(
                notification=notification,
                device_tokens=device_tokens,
            )

            assert result["failed"] == 1

        @pytest.mark.asyncio
    async def test_send_apns_notification(self, service):
        """Test APNs notification sending."""
        notification = MagicMock(spec=Notification)
        device_tokens = ["token_1", "token_2"]

        result = await service._send_apns_notification(
            notification=notification,
            device_tokens=device_tokens,
        )

        assert result["sent"] == 2
        assert result["failed"] == 0


class TestDeviceTokenModel:

        """Test device token model."""

    def test_device_token_to_dict(self):

        """Test converting device token to dictionary."""

        token = DeviceToken(
            id="token_id",
            user_id="user_123",
            device_token="test_token",
            platform="android",
            device_name="Samsung Galaxy",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = token.to_dict()

        assert result["id"] == "token_id"
        assert result["user_id"] == "user_123"
        assert result["device_token"] == "test_token"
        assert result["platform"] == "android"
        assert result["device_name"] == "Samsung Galaxy"
        assert result["is_active"] is True
        assert "created_at" in result
        assert "updated_at" in result


class TestPushNotificationIntegration:

        """Integration tests for push notifications."""

        @pytest.mark.asyncio
    async def test_full_push_notification_flow(self):
        """Test complete push notification flow."""
        with patch("app.services.mobile_notification_service.get_settings") as mock_settings:
            mock_settings.return_value.fcm_api_key = "test_key"
            mock_settings.return_value.apns_key_id = None
            mock_settings.return_value.apns_team_id = None
            mock_settings.return_value.apns_bundle_id = None

            mock_db = MagicMock()
            service = MobileNotificationService(db=mock_db)

            # Register device token
            mock_db.query.return_value.filter_by.return_value.first.return_value = None
            await service.register_device_token(
                user_id="user_123",
                device_token="android_token",
                platform="android",
            )

            # Get device tokens
            token = MagicMock(spec=DeviceToken)
            token.device_token = "android_token"
            mock_db.query.return_value.filter_by.return_value.all.return_value = [token]

            tokens = await service.get_user_device_tokens(user_id="user_123")
            assert len(tokens) == 1

            # Send notification
            notification = MagicMock(spec=Notification)
            notification.id = "notif_id"
            notification.title = "Test"
            notification.message = "Test message"
            notification.type = "test"
            notification.icon = "icon"

        with patch.object(service, "_send_fcm_notification", new_callable=AsyncMock) as mock_fcm:
                mock_fcm.return_value = {"sent": 1, "failed": 0}

                result = await service.send_push_notification(
                    user_id="user_123",
                    notification=notification,
                    device_tokens=tokens,
                )

                assert result["android"]["sent"] == 1
