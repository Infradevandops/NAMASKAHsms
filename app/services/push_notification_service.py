"""Push notification service using Firebase Cloud Messaging"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.device_token import DeviceToken
from app.models.user import User

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""

    def __init__(self):
        self.fcm_server_key = getattr(settings, "FCM_SERVER_KEY", None)
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.vapid_key = getattr(settings, "FCM_VAPID_KEY", None)

    def _is_configured(self) -> bool:
        """Check if FCM is properly configured"""
        return bool(self.fcm_server_key)

    async def send_to_user(
        self,
        db: Session,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: str = "/static/icons/icon-192x192.png",
        badge: str = "/static/icons/badge-72x72.png",
        tag: Optional[str] = None,
        require_interaction: bool = False,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to all user's active devices

        Args:
            db: Database session
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            icon: Notification icon URL
            badge: Badge icon URL
            tag: Notification tag (for grouping)
            require_interaction: Keep notification until user interacts
            actions: Notification action buttons

        Returns:
            Dict with success status and delivery stats
        """
        if not self._is_configured():
            logger.warning("FCM not configured, skipping push notification")
            return {"success": False, "error": "FCM not configured"}

        # Get user's active devices
        devices = (
            db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.active == True)
            .all()
        )

        if not devices:
            logger.debug(f"No active devices for user {user_id}")
            return {"success": True, "sent": 0, "message": "No active devices"}

        # Filter out expired tokens
        active_devices = [d for d in devices if not d.is_expired()]

        if not active_devices:
            logger.debug(f"All devices expired for user {user_id}")
            return {"success": True, "sent": 0, "message": "All devices expired"}

        # Send to all devices
        results = []
        for device in active_devices:
            result = await self.send_to_device(
                device.token,
                title,
                body,
                data=data,
                icon=icon,
                badge=badge,
                tag=tag,
                require_interaction=require_interaction,
                actions=actions,
            )
            results.append(result)

            if result.get("success"):
                # Update last_used_at
                device.last_used_at = datetime.utcnow()
                db.commit()

        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        return {
            "success": successful > 0,
            "sent": successful,
            "failed": failed,
            "total_devices": len(active_devices),
        }

    async def send_to_device(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: str = "/static/icons/icon-192x192.png",
        badge: str = "/static/icons/badge-72x72.png",
        tag: Optional[str] = None,
        require_interaction: bool = False,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to a specific device

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            icon: Notification icon URL
            badge: Badge icon URL
            tag: Notification tag
            require_interaction: Keep notification until user interacts
            actions: Notification action buttons

        Returns:
            Dict with success status
        """
        if not self._is_configured():
            return {"success": False, "error": "FCM not configured"}

        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "icon": icon,
                "badge": badge,
                "click_action": "FCM_PLUGIN_ACTIVITY",
            },
            "data": data or {},
            "priority": "high",
            "webpush": {
                "headers": {"Urgency": "high"},
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": icon,
                    "badge": badge,
                    "tag": tag or "default",
                    "requireInteraction": require_interaction,
                    "actions": actions or [],
                },
            },
        }

        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.fcm_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success") == 1:
                    logger.info(
                        f"Push notification sent successfully to token {token[:20]}..."
                    )
                    return {
                        "success": True,
                        "message_id": result.get("results", [{}])[0].get("message_id"),
                    }
                else:
                    error = result.get("results", [{}])[0].get("error", "Unknown error")
                    logger.warning(f"FCM error: {error}")
                    return {"success": False, "error": error}

        except httpx.HTTPStatusError as e:
            logger.error(
                f"FCM HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return {"success": False, "error": str(e)}

    async def send_sms_notification(
        self,
        db: Session,
        user_id: int,
        service: str,
        sms_code: str,
        verification_id: int,
    ) -> Dict[str, Any]:
        """Send notification when SMS code is received"""
        return await self.send_to_user(
            db=db,
            user_id=user_id,
            title="🔔 SMS Code Received",
            body=f"{service}: {sms_code}",
            data={
                "type": "sms_received",
                "verification_id": str(verification_id),
                "sms_code": sms_code,
                "service": service,
                "url": "/verify",
            },
            tag="sms-verification",
            require_interaction=True,
            actions=[
                {"action": "view", "title": "View Code"},
                {"action": "copy", "title": "Copy Code"},
            ],
        )

    async def send_payment_notification(
        self, db: Session, user_id: int, amount: float, currency: str = "USD"
    ) -> Dict[str, Any]:
        """Send notification when payment is completed"""
        return await self.send_to_user(
            db=db,
            user_id=user_id,
            title="💳 Payment Successful",
            body=f"${amount:.2f} {currency} added to your wallet",
            data={
                "type": "payment_completed",
                "amount": str(amount),
                "currency": currency,
                "url": "/wallet",
            },
            tag="payment",
            actions=[{"action": "view", "title": "View Wallet"}],
        )

    async def send_low_balance_alert(
        self, db: Session, user_id: int, balance: float
    ) -> Dict[str, Any]:
        """Send notification when balance is low"""
        return await self.send_to_user(
            db=db,
            user_id=user_id,
            title="⚠️ Low Balance Alert",
            body=f"Your balance is ${balance:.2f}. Add credits to continue.",
            data={"type": "low_balance", "balance": str(balance), "url": "/wallet"},
            tag="low-balance",
            require_interaction=True,
            actions=[{"action": "topup", "title": "Add Credits"}],
        )

    async def register_device(
        self,
        db: Session,
        user_id: int,
        token: str,
        platform: str = "web",
        device_type: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> DeviceToken:
        """
        Register a new device token

        Args:
            db: Database session
            user_id: User ID
            token: FCM device token
            platform: Platform (web, ios, android)
            device_type: Device type (browser name, device model)
            device_name: User-friendly device name

        Returns:
            DeviceToken object
        """
        # Check if token already exists
        existing = db.query(DeviceToken).filter(DeviceToken.token == token).first()

        if existing:
            # Reactivate if inactive
            if not existing.active:
                existing.active = True
            existing.refresh_expiry()
            db.commit()
            db.refresh(existing)
            return existing

        # Create new device token
        device = DeviceToken(
            user_id=user_id,
            token=token,
            platform=platform,
            device_type=device_type,
            device_name=device_name,
            active=True,
        )
        device.refresh_expiry()

        db.add(device)
        db.commit()
        db.refresh(device)

        logger.info(f"Registered new device for user {user_id}: {platform}")
        return device

    async def unregister_device(self, db: Session, user_id: int, token: str) -> bool:
        """
        Unregister a device token

        Args:
            db: Database session
            user_id: User ID
            token: FCM device token

        Returns:
            True if unregistered successfully
        """
        device = (
            db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.token == token)
            .first()
        )

        if not device:
            return False

        device.active = False
        db.commit()

        logger.info(f"Unregistered device for user {user_id}")
        return True

    async def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Remove expired device tokens

        Returns:
            Number of tokens removed
        """
        expired = (
            db.query(DeviceToken)
            .filter(DeviceToken.expires_at < datetime.utcnow())
            .all()
        )

        count = len(expired)
        for device in expired:
            db.delete(device)

        db.commit()
        logger.info(f"Cleaned up {count} expired device tokens")
        return count


# Singleton instance
push_notification_service = PushNotificationService()
