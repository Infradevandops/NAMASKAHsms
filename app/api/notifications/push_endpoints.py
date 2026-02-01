"""Push notification endpoints for mobile devices."""


from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user_id, get_db
from app.core.logging import get_logger
from app.models.device_token import DeviceToken
from app.services.mobile_notification_service import MobileNotificationService
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.notification_preference import NotificationPreference

logger = get_logger(__name__)

router = APIRouter(prefix="/api/notifications/push", tags=["Push Notifications"])


@router.post("/register-device")
async def register_device_token(
    device_token: str = Query(..., min_length=10),
    platform: str = Query(..., pattern="^(ios|android)$"),
    device_name: Optional[str] = Query(None, max_length=255),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Register device token for push notifications.

    Args:
        device_token: Device token from FCM or APNs
        platform: 'ios' or 'android'
        device_name: Optional device name
        user_id: Current user ID
        db: Database session

    Returns:
        Success message with device token info
    """
try:
        service = MobileNotificationService(db=db)
        success = await service.register_device_token(
            user_id=user_id,
            device_token=device_token,
            platform=platform,
            device_name=device_name,
        )

if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register device token",
            )

        logger.info(f"Device token registered for user {user_id}")

        return {
            "success": True,
            "message": "Device token registered successfully",
            "device_token": device_token,
            "platform": platform,
        }

except Exception as e:
        logger.error(f"Error registering device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token",
        )


@router.post("/unregister-device")
async def unregister_device_token(
    device_token: str = Query(..., min_length=10),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Unregister device token.

    Args:
        device_token: Device token to unregister
        user_id: Current user ID
        db: Database session

    Returns:
        Success message
    """
try:
        service = MobileNotificationService(db=db)
        success = await service.unregister_device_token(
            user_id=user_id,
            device_token=device_token,
        )

if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found",
            )

        logger.info(f"Device token unregistered for user {user_id}")

        return {
            "success": True,
            "message": "Device token unregistered successfully",
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error unregistering device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token",
        )


@router.get("/devices")
async def get_user_devices(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's registered devices.

    Args:
        user_id: Current user ID
        db: Database session

    Returns:
        List of registered devices
    """
try:
        devices = (
            db.query(DeviceToken)
            .filter_by(
                user_id=user_id,
                is_active=True,
            )
            .all()
        )

        return {
            "success": True,
            "devices": [device.to_dict() for device in devices],
            "total": len(devices),
        }

except Exception as e:
        logger.error(f"Error getting user devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get devices",
        )


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a registered device.

    Args:
        device_id: Device ID to delete
        user_id: Current user ID
        db: Database session

    Returns:
        Success message
    """
try:
        device = (
            db.query(DeviceToken)
            .filter_by(
                id=device_id,
                user_id=user_id,
            )
            .first()
        )

if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        device.is_active = False
        db.commit()

        logger.info(f"Device {device_id} deleted for user {user_id}")

        return {
            "success": True,
            "message": "Device deleted successfully",
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device",
        )


@router.post("/test")
async def send_test_push_notification(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Send test push notification to user's devices.

    Args:
        user_id: Current user ID
        db: Database session

    Returns:
        Results of push notification delivery
    """
try:

        # Get user's active devices
        devices = (
            db.query(DeviceToken)
            .filter_by(
                user_id=user_id,
                is_active=True,
            )
            .all()
        )

if not devices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered devices found",
            )

        # Create test notification
        test_notification = Notification(
            user_id=user_id,
            type="test",
            title="Test Notification",
            message="This is a test push notification from Namaskah",
            icon="ic_notification",
        )

        # Send push notification
        service = MobileNotificationService(db=db)
        device_tokens = [d.device_token for d in devices]
        results = await service.send_push_notification(
            user_id=user_id,
            notification=test_notification,
            device_tokens=device_tokens,
        )

        logger.info(f"Test push notification sent for user {user_id}")

        return {
            "success": True,
            "message": "Test push notification sent",
            "results": results,
            "devices_count": len(devices),
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error sending test push notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test push notification",
        )


@router.get("/preferences")
async def get_push_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's push notification preferences.

    Args:
        user_id: Current user ID
        db: Database session

    Returns:
        Push notification preferences
    """
try:

        preferences = (
            db.query(NotificationPreference)
            .filter_by(
                user_id=user_id,
            )
            .all()
        )

        # Filter for push-enabled preferences
        push_preferences = [p.to_dict() for p in preferences if "push" in (p.delivery_methods or "").lower()]

        return {
            "success": True,
            "preferences": push_preferences,
            "total": len(push_preferences),
        }

except Exception as e:
        logger.error(f"Error getting push preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get push preferences",
        )


@router.put("/preferences/{notification_type}")
async def update_push_preference(
    notification_type: str,
    enabled: bool = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update push notification preference for a notification type.

    Args:
        notification_type: Type of notification
        enabled: Whether to enable push for this type
        user_id: Current user ID
        db: Database session

    Returns:
        Updated preference
    """
try:

        preference = (
            db.query(NotificationPreference)
            .filter_by(
                user_id=user_id,
                notification_type=notification_type,
            )
            .first()
        )

if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preference not found",
            )

        # Update delivery methods
        methods = set((preference.delivery_methods or "").split(","))
if enabled:
            methods.add("push")
else:
            methods.discard("push")

        preference.delivery_methods = ",".join(filter(None, methods))
        db.commit()

        logger.info(f"Push preference updated for user {user_id} ({notification_type})")

        return {
            "success": True,
            "message": "Push preference updated",
            "preference": preference.to_dict(),
        }

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error updating push preference: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update push preference",
        )
