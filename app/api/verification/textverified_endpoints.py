"""TextVerified SMS endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)
router = APIRouter(prefix="/verification/textverified", tags=["TextVerified"])


@router.get("/health")
async def textverified_health() -> Dict[str, Any]:
    """Get TextVerified service health status with balance."""
    try:
        logger.info("Health check endpoint called")
        service = TextVerifiedService()
        health_status = await service.get_health_status()

        if health_status.get("status") == "operational":
            logger.info("Health check successful - service operational")
            return health_status
        elif (
            "credentials" in health_status.get("error", "").lower()
            or "not configured" in health_status.get("error", "").lower()
        ):
            logger.warning(
                f"Health check failed - invalid credentials: {health_status.get('error')}"
            )
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid credentials",
                    "details": health_status.get("error", "Invalid credentials"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            logger.error(
                f"Health check failed - service unavailable: {health_status.get('error')}"
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "TextVerified service unavailable",
                    "details": health_status.get(
                        "error", "TextVerified service unavailable"
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check endpoint error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "TextVerified service unavailable",
                "details": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@router.get("/balance")
async def get_balance() -> Dict[str, Any]:
    """Get TextVerified account balance."""
    try:
        logger.info("Balance endpoint called")
        service = TextVerifiedService()
        balance_data = await service.get_balance()
        logger.info(
            f"Balance retrieved: {balance_data['balance']} {balance_data['currency']}"
        )
        return balance_data
    except Exception as e:
        logger.error(f"Balance endpoint error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Failed to retrieve balance",
                "details": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get TextVerified service status (legacy endpoint)."""
    logger.debug("Status endpoint called")
    return {"status": "operational"}


@router.get("/services")
async def get_services() -> Dict[str, Any]:
    """Get available services from TextVerified API."""
    try:
        logger.info("Services endpoint called")
        service = TextVerifiedService()

        if not service.enabled:
            fallback_services = [
                {"id": "telegram", "name": "Telegram", "cost": 0.50},
                {"id": "whatsapp", "name": "WhatsApp", "cost": 0.75},
                {"id": "google", "name": "Google", "cost": 0.50},
                {"id": "facebook", "name": "Facebook", "cost": 0.60},
                {"id": "instagram", "name": "Instagram", "cost": 0.65},
                {"id": "twitter", "name": "Twitter", "cost": 0.55},
                {"id": "discord", "name": "Discord", "cost": 0.45},
                {"id": "tiktok", "name": "TikTok", "cost": 0.70},
            ]
            logger.warning("TextVerified not configured, using fallback services")
            return {
                "success": True,
                "services": fallback_services,
                "total": len(fallback_services),
                "source": "fallback",
            }

        services_list = await service.get_services_list()
        logger.info(f"Retrieved {len(services_list)} services from TextVerified API")

        return {
            "success": True,
            "services": services_list,
            "total": len(services_list),
            "source": "textverified_api",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Services endpoint error: {str(e)}")
        fallback_services = [
            {"id": "telegram", "name": "Telegram", "cost": 0.50},
            {"id": "whatsapp", "name": "WhatsApp", "cost": 0.75},
            {"id": "google", "name": "Google", "cost": 0.50},
            {"id": "facebook", "name": "Facebook", "cost": 0.60},
        ]
        logger.warning(f"TextVerified API failed, using fallback: {str(e)}")
        return {
            "success": True,
            "services": fallback_services,
            "total": len(fallback_services),
            "source": "fallback",
            "error": str(e),
        }
