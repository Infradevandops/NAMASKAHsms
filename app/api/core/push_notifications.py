"""Push notification API endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.device_token import DeviceToken
from app.models.user import User
from app.services.push_notification_service import push_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/push", tags=["push-notifications"])


# Schemas
class DeviceRegistrationRequest(BaseModel):
    """Device registration request"""

    token: str = Field(..., description="FCM device token")
    platform: str = Field(default="web", description="Platform: web, ios, android")
    device_type: Optional[str] = Field(None, description="Browser name or device model")
    device_name: Optional[str] = Field(None, description="User-friendly device name")


class DeviceResponse(BaseModel):
    """Device token response"""

    id: int
    token: str
    platform: str
    device_type: Optional[str]
    device_name: Optional[str]
    active: bool
    last_used_at: Optional[str]
    expires_at: Optional[str]
    created_at: Optional[str]


class DeviceListResponse(BaseModel):
    """List of devices"""

    devices: list[DeviceResponse]
    total: int


# Endpoints
@router.post("/register", response_model=DeviceResponse)
async def register_device(
    request: DeviceRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a device for push notifications

    The device token should be obtained from Firebase SDK on the client side.
    """
    try:
        device = await push_notification_service.register_device(
            db=db,
            user_id=current_user.id,
            token=request.token,
            platform=request.platform,
            device_type=request.device_type,
            device_name=request.device_name,
        )

        return DeviceResponse(
            id=device.id,
            token=device.token,
            platform=device.platform,
            device_type=device.device_type,
            device_name=device.device_name,
            active=device.active,
            last_used_at=(
                device.last_used_at.isoformat() if device.last_used_at else None
            ),
            expires_at=device.expires_at.isoformat() if device.expires_at else None,
            created_at=device.created_at.isoformat() if device.created_at else None,
        )
    except Exception as e:
        logger.error(f"Failed to register device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device",
        )


@router.delete("/unregister")
async def unregister_device(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unregister a device from push notifications"""
    success = await push_notification_service.unregister_device(
        db=db, user_id=current_user.id, token=token
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    return {"message": "Device unregistered successfully"}


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List all registered devices for the current user"""
    devices = db.query(DeviceToken).filter(DeviceToken.user_id == current_user.id).all()

    device_list = [
        DeviceResponse(
            id=d.id,
            token=(
                d.token[:20] + "..." if len(d.token) > 20 else d.token
            ),  # Truncate for security
            platform=d.platform,
            device_type=d.device_type,
            device_name=d.device_name,
            active=d.active,
            last_used_at=d.last_used_at.isoformat() if d.last_used_at else None,
            expires_at=d.expires_at.isoformat() if d.expires_at else None,
            created_at=d.created_at.isoformat() if d.created_at else None,
        )
        for d in devices
    ]

    return DeviceListResponse(devices=device_list, total=len(device_list))


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a specific device"""
    device = (
        db.query(DeviceToken)
        .filter(DeviceToken.id == device_id, DeviceToken.user_id == current_user.id)
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    db.delete(device)
    db.commit()

    return {"message": "Device removed successfully"}


@router.post("/test")
async def send_test_notification(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Send a test push notification to all user's devices"""
    result = await push_notification_service.send_to_user(
        db=db,
        user_id=current_user.id,
        title="✅ Test Notification",
        body="Push notifications are working! You'll receive alerts for SMS codes, payments, and more.",
        data={"type": "test", "url": "/dashboard"},
        tag="test",
        actions=[{"action": "view", "title": "Open Dashboard"}],
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send test notification"),
        )

    return {
        "message": "Test notification sent successfully",
        "sent": result.get("sent", 0),
        "total_devices": result.get("total_devices", 0),
    }


@router.get("/config")
async def get_push_config():
    """Get public push notification configuration (VAPID key)"""
    from app.core.config import settings

    vapid_key = getattr(settings, "FCM_VAPID_KEY", None)

    if not vapid_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications not configured",
        )

    return {"vapid_key": vapid_key, "enabled": True}
