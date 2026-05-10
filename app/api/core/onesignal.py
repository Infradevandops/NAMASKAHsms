"""OneSignal push notification endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.device_token import DeviceToken
from app.models.user import User
from app.services.onesignal_service import onesignal_service

router = APIRouter(prefix="/onesignal", tags=["OneSignal Push Notifications"])
logger = logging.getLogger(__name__)


class RegisterDeviceRequest(BaseModel):
    player_id: str
    device_type: str = "web"


class UnregisterDeviceRequest(BaseModel):
    player_id: str


class TestNotificationRequest(BaseModel):
    title: str = "Test Notification"
    message: str = "This is a test notification from Namaskah"


@router.post("/register")
async def register_device(
    request: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register device for push notifications"""
    try:
        success = await onesignal_service.register_device(
            db, current_user.id, request.player_id, request.device_type
        )

        if success:
            return {
                "success": True,
                "message": "Device registered successfully",
                "player_id": request.player_id,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to register device")

    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unregister")
async def unregister_device(
    request: UnregisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unregister device from push notifications"""
    try:
        success = await onesignal_service.unregister_device(
            db, current_user.id, request.player_id
        )

        if success:
            return {
                "success": True,
                "message": "Device unregistered successfully",
            }
        else:
            raise HTTPException(status_code=404, detail="Device not found")

    except Exception as e:
        logger.error(f"Error unregistering device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices")
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's registered devices"""
    devices = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == current_user.id,
            DeviceToken.active == True,
        )
        .all()
    )

    return {
        "devices": [
            {
                "id": device.id,
                "device_type": device.device_type,
                "registered_at": device.created_at.isoformat(),
                "last_used": (
                    device.last_used_at.isoformat() if device.last_used_at else None
                ),
            }
            for device in devices
        ]
    }


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a specific device"""
    device = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.id == device_id,
            DeviceToken.user_id == current_user.id,
        )
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.active = False
    db.commit()

    return {"success": True, "message": "Device removed successfully"}


@router.post("/test")
async def send_test_notification(
    request: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a test notification to current user"""
    try:
        success = await onesignal_service.send_to_user(
            db, current_user.id, request.title, request.message
        )

        if success:
            return {
                "success": True,
                "message": "Test notification sent successfully",
            }
        else:
            return {
                "success": False,
                "message": "No active devices found or notification failed",
            }

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    """Get OneSignal configuration for frontend"""
    return {
        "app_id": onesignal_service.app_id,
        "enabled": bool(onesignal_service.app_id and onesignal_service.api_key),
    }
