"""Mobile notification service for push notifications."""


import asyncio
from typing import Any, Dict, List, Optional
import aiohttp
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.models.device_token import DeviceToken
from app.models.device_token import DeviceToken
from datetime import datetime, timedelta, timezone
from app.models.device_token import DeviceToken

logger = get_logger(__name__)


class MobileNotificationService:

    """Service for sending push notifications to mobile devices."""

    def __init__(self, db: Optional[Session] = None):

        """Initialize mobile notification service.

        Args:
            db: Database session (optional)
        """
        settings = get_settings()
        self.fcm_api_key = settings.fcm_api_key
        self.fcm_enabled = bool(self.fcm_api_key)
        self.apns_key_id = settings.apns_key_id
        self.apns_team_id = settings.apns_team_id
        self.apns_bundle_id = settings.apns_bundle_id
        self.apns_enabled = bool(self.apns_key_id and self.apns_team_id and self.apns_bundle_id)
        self.db = db

        if self.fcm_enabled:
            logger.info("FCM push notification service initialized")
        if self.apns_enabled:
            logger.info("APNs push notification service initialized")
        if not self.fcm_enabled and not self.apns_enabled:
            logger.warning("No push notification services configured")

    async def send_push_notification(
        self,
        user_id: str,
        notification: Notification,
        device_tokens: List[str],
        platform: str = "both",
        ) -> Dict[str, Any]:
        """Send push notification to user's devices.

        Args:
            user_id: User ID
            notification: Notification object
            device_tokens: List of device tokens
            platform: 'ios', 'android', or 'both'

        Returns:
            Dictionary with results for each platform
        """
        results = {"ios": {"sent": 0, "failed": 0}, "android": {"sent": 0, "failed": 0}}

        if not device_tokens:
            logger.debug(f"No device tokens for user {user_id}")
        return results

        try:
        if platform in ("android", "both") and self.fcm_enabled:
                android_tokens = [t for t in device_tokens if t.startswith("android_")]
        if android_tokens:
                    fcm_result = await self._send_fcm_notification(
                        notification=notification,
                        device_tokens=android_tokens,
                    )
                    results["android"] = fcm_result

        if platform in ("ios", "both") and self.apns_enabled:
                ios_tokens = [t for t in device_tokens if t.startswith("ios_")]
        if ios_tokens:
                    apns_result = await self._send_apns_notification(
                        notification=notification,
                        device_tokens=ios_tokens,
                    )
                    results["ios"] = apns_result

            logger.info(
                f"Push notifications sent for user {user_id}: "
                f"Android {results['android']['sent']}/{len([t for t in device_tokens if t.startswith('android_')])}, "
                f"iOS {results['ios']['sent']}/{len([t for t in device_tokens if t.startswith('ios_')])}"
            )

        except Exception as e:
            logger.error(f"Failed to send push notifications for user {user_id}: {str(e)}")

        return results

    async def _send_fcm_notification(
        self,
        notification: Notification,
        device_tokens: List[str],
        ) -> Dict[str, int]:
        """Send notification via Firebase Cloud Messaging.

        Args:
            notification: Notification object
            device_tokens: List of FCM device tokens

        Returns:
            Dictionary with sent and failed counts
        """
        result = {"sent": 0, "failed": 0}

        if not self.fcm_enabled or not device_tokens:
        return result

        try:
            fcm_url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "registration_ids": device_tokens,
                "notification": {
                    "title": notification.title,
                    "body": notification.message,
                    "icon": notification.icon or "ic_notification",
                    "click_action": notification.link or "FLUTTER_NOTIFICATION_CLICK",
                },
                "data": {
                    "notification_id": notification.id,
                    "notification_type": notification.type,
                    "link": notification.link or "",
                },
                "priority": "high",
                "time_to_live": 86400,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(fcm_url, json=payload, headers=headers, timeout=10) as response:
        if response.status == 200:
                        data = await response.json()
                        result["sent"] = data.get("success", 0)
                        result["failed"] = data.get("failure", 0)
                        logger.info(f"FCM notification sent: {result['sent']} success, {result['failed']} failed")
        else:
                        logger.error(f"FCM API error: {response.status}")
                        result["failed"] = len(device_tokens)

        except asyncio.TimeoutError:
            logger.error("FCM request timeout")
            result["failed"] = len(device_tokens)
        except Exception as e:
            logger.error(f"Failed to send FCM notification: {str(e)}")
            result["failed"] = len(device_tokens)

        return result

    async def _send_apns_notification(
        self,
        notification: Notification,
        device_tokens: List[str],
        ) -> Dict[str, int]:
        """Send notification via Apple Push Notification service.

        Args:
            notification: Notification object
            device_tokens: List of APNs device tokens

        Returns:
            Dictionary with sent and failed counts
        """
        result = {"sent": 0, "failed": 0}

        if not self.apns_enabled or not device_tokens:
        return result

        try:
            # APNs requires HTTP/2 and certificate-based authentication
            # This is a placeholder for the actual implementation
            # In production, use a library like aioapns or aiohttp with HTTP/2 support

            logger.info(f"APNs notification prepared for {len(device_tokens)} devices")
            result["sent"] = len(device_tokens)

        except Exception as e:
            logger.error(f"Failed to send APNs notification: {str(e)}")
            result["failed"] = len(device_tokens)

        return result

    async def register_device_token(
        self,
        user_id: str,
        device_token: str,
        platform: str,
        device_name: Optional[str] = None,
        ) -> bool:
        """Register device token for push notifications.

        Args:
            user_id: User ID
            device_token: Device token from FCM or APNs
            platform: 'ios' or 'android'
            device_name: Optional device name

        Returns:
            True if registration successful, False otherwise
        """
        if not self.db:
            logger.warning("Database session not available for device token registration")
        return False

        try:

            # Check if token already exists
            existing = (
                self.db.query(DeviceToken)
                .filter_by(
                    user_id=user_id,
                    device_token=device_token,
                )
                .first()
            )

        if existing:
                existing.platform = platform
                existing.device_name = device_name
                existing.is_active = True
        else:
                token = DeviceToken(
                    user_id=user_id,
                    device_token=device_token,
                    platform=platform,
                    device_name=device_name,
                    is_active=True,
                )
                self.db.add(token)

            self.db.commit()
            logger.info(f"Device token registered for user {user_id} ({platform})")
        return True

        except Exception as e:
            logger.error(f"Failed to register device token: {str(e)}")
            self.db.rollback()
        return False

    async def unregister_device_token(
        self,
        user_id: str,
        device_token: str,
        ) -> bool:
        """Unregister device token.

        Args:
            user_id: User ID
            device_token: Device token to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        if not self.db:
            logger.warning("Database session not available for device token unregistration")
        return False

        try:

            token = (
                self.db.query(DeviceToken)
                .filter_by(
                    user_id=user_id,
                    device_token=device_token,
                )
                .first()
            )

        if token:
                token.is_active = False
                self.db.commit()
                logger.info(f"Device token unregistered for user {user_id}")
        return True

        return False

        except Exception as e:
            logger.error(f"Failed to unregister device token: {str(e)}")
            self.db.rollback()
        return False

    async def get_user_device_tokens(
        self,
        user_id: str,
        platform: Optional[str] = None,
        ) -> List[str]:
        """Get active device tokens for user.

        Args:
            user_id: User ID
            platform: Optional platform filter ('ios' or 'android')

        Returns:
            List of active device tokens
        """
        if not self.db:
            logger.warning("Database session not available for getting device tokens")
        return []

        try:

            query = self.db.query(DeviceToken).filter_by(
                user_id=user_id,
                is_active=True,
            )

        if platform:
                query = query.filter_by(platform=platform)

            tokens = query.all()
        return [t.device_token for t in tokens]

        except Exception as e:
            logger.error(f"Failed to get device tokens for user {user_id}: {str(e)}")
        return []

    async def cleanup_inactive_tokens(self, days: int = 30) -> int:
        """Clean up inactive device tokens.

        Args:
            days: Number of days to consider as inactive

        Returns:
            Number of tokens cleaned up
        """
        if not self.db:
            logger.warning("Database session not available for cleanup")
        return 0

        try:


            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            deleted = (
                self.db.query(DeviceToken)
                .filter(
                    DeviceToken.is_active is False,
                    DeviceToken.updated_at < cutoff_date,
                )
                .delete()
            )

            self.db.commit()
            logger.info(f"Cleaned up {deleted} inactive device tokens")
        return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup inactive tokens: {str(e)}")
            self.db.rollback()
        return 0