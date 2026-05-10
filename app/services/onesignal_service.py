"""OneSignal push notification service"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.device_token import DeviceToken
from app.models.user import User

logger = logging.getLogger(__name__)


class OneSignalService:
    """Service for sending push notifications via OneSignal"""

    def __init__(self):
        self.app_id = getattr(settings, "ONESIGNAL_APP_ID", None)
        self.api_key = getattr(settings, "ONESIGNAL_API_KEY", None)
        self.base_url = "https://onesignal.com/api/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_notification(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to specific users

        Args:
            user_ids: List of user IDs to send to
            title: Notification title
            message: Notification message
            data: Additional data payload
            url: URL to open when clicked

        Returns:
            API response dict
        """
        if not self.app_id or not self.api_key:
            logger.warning("OneSignal not configured, skipping notification")
            return {"ok": False, "error": "OneSignal not configured"}

        payload = {
            "app_id": self.app_id,
            "headings": {"en": title},
            "contents": {"en": message},
            "filters": [
                {"field": "tag", "key": "user_id", "relation": "=", "value": user_id}
                for user_id in user_ids
            ],
        }

        if data:
            payload["data"] = data

        if url:
            payload["url"] = url

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/notifications",
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()
                logger.info(
                    f"OneSignal notification sent to {len(user_ids)} users",
                    extra={"recipients": result.get("recipients", 0)},
                )
                return {"ok": True, "data": result}

        except httpx.HTTPStatusError as e:
            logger.error(f"OneSignal API error: {e.response.status_code}")
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Failed to send OneSignal notification: {e}")
            return {"ok": False, "error": str(e)}

    async def send_to_user(
        self,
        db: Session,
        user_id: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
    ) -> bool:
        """
        Send notification to a single user

        Args:
            db: Database session
            user_id: User ID
            title: Notification title
            message: Notification message
            data: Additional data
            url: URL to open

        Returns:
            True if sent successfully
        """
        # Check if user has active device tokens
        active_tokens = (
            db.query(DeviceToken)
            .filter(
                DeviceToken.user_id == user_id,
                DeviceToken.active == True,
                DeviceToken.device_type == "web",
            )
            .count()
        )

        if active_tokens == 0:
            logger.debug(f"No active push tokens for user {user_id}")
            return False

        result = await self.send_notification([user_id], title, message, data, url)
        return result.get("ok", False)

    async def send_sms_notification(
        self, db: Session, user_id: str, verification_id: str, sms_code: str
    ) -> bool:
        """Send notification when SMS code is received"""
        title = "🔔 SMS Code Received"
        message = f"Your verification code: {sms_code}"
        data = {
            "type": "sms_received",
            "verification_id": verification_id,
            "code": sms_code,
        }
        url = f"/verify/{verification_id}"

        return await self.send_to_user(db, user_id, title, message, data, url)

    async def send_payment_notification(
        self, db: Session, user_id: str, amount: float, status: str
    ) -> bool:
        """Send notification for payment events"""
        if status == "success":
            title = "✅ Payment Successful"
            message = f"${amount:.2f} added to your account"
        else:
            title = "❌ Payment Failed"
            message = f"Payment of ${amount:.2f} failed"

        data = {"type": "payment", "amount": amount, "status": status}
        url = "/wallet"

        return await self.send_to_user(db, user_id, title, message, data, url)

    async def send_low_balance_alert(
        self, db: Session, user_id: str, balance: float, threshold: float
    ) -> bool:
        """Send low balance alert"""
        title = "⚠️ Low Balance Alert"
        message = f"Your balance (${balance:.2f}) is below ${threshold:.2f}"
        data = {"type": "low_balance", "balance": balance, "threshold": threshold}
        url = "/wallet"

        return await self.send_to_user(db, user_id, title, message, data, url)

    async def register_device(
        self, db: Session, user_id: str, player_id: str, device_type: str = "web"
    ) -> bool:
        """
        Register device with OneSignal and store player_id

        Args:
            db: Database session
            user_id: User ID
            player_id: OneSignal player ID
            device_type: Device type (web, ios, android)

        Returns:
            True if registered successfully
        """
        # Check if device already exists
        existing = (
            db.query(DeviceToken)
            .filter(
                DeviceToken.user_id == user_id,
                DeviceToken.token == player_id,
                DeviceToken.device_type == device_type,
            )
            .first()
        )

        if existing:
            # Update last used
            existing.last_used_at = datetime.utcnow()
            existing.active = True
            db.commit()
            logger.info(f"Updated existing device token for user {user_id}")
            return True

        # Create new device token
        device_token = DeviceToken(
            user_id=user_id,
            token=player_id,
            device_type=device_type,
            active=True,
            last_used_at=datetime.utcnow(),
        )

        db.add(device_token)
        db.commit()
        logger.info(f"Registered new device token for user {user_id}")
        return True

    async def unregister_device(
        self, db: Session, user_id: str, player_id: str
    ) -> bool:
        """Unregister device"""
        device = (
            db.query(DeviceToken)
            .filter(
                DeviceToken.user_id == user_id,
                DeviceToken.token == player_id,
            )
            .first()
        )

        if device:
            device.active = False
            db.commit()
            logger.info(f"Unregistered device token for user {user_id}")
            return True

        return False

    async def send_bulk_notification(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        return await self.send_notification(user_ids, title, message, data)


# Singleton instance
onesignal_service = OneSignalService()
