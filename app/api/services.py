"""
Services API Router - SMS Service Management
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/status")
async def get_services_status():
    """Get status of all SMS services"""
    return {
        "status": "operational",
        "services": {
            "sms_activate": "active",
            "5sim": "active",
            "textverified": "active",
            "getsms": "active",
        },
    }


@router.get("/providers")
async def get_providers(current_user: User = Depends(get_current_user)):
    """Get available SMS providers"""
    return {
        "providers": [
            {"name": "SMS-Activate", "status": "active", "countries": 180},
            {"name": "5SIM", "status": "active", "countries": 150},
            {"name": "TextVerified", "status": "active", "countries": 50},
            {"name": "GetSMS", "status": "active", "countries": 100},
        ]
    }
