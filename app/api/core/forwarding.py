"""SMS forwarding configuration API."""
from app.core.logging import get_logger
from app.core.dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/forwarding", tags=["Forwarding"])


@router.post("/configure")
async def configure_forwarding(
    email_enabled: bool = False,
    email_address: str = None,
    webhook_enabled: bool = False,
    webhook_url: str = None,
    webhook_secret: str = None,
    forward_all: bool = True,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Configure SMS forwarding settings."""
    try:
        # Get or create config
        config = db.query(ForwardingConfig).filter(
            ForwardingConfig.user_id == user_id
        ).first()

        if not config:
            config = ForwardingConfig(user_id=user_id)
            db.add(config)

        # Update settings
        config.email_enabled = email_enabled
        config.email_address = email_address
        config.webhook_enabled = webhook_enabled
        config.webhook_url = webhook_url
        config.webhook_secret = webhook_secret
        config.forward_all = forward_all
        config.is_active = email_enabled or webhook_enabled

        db.commit()

        return {
            "success": True,
            "message": "Forwarding configured successfully",
            "config": {
                "email_enabled": config.email_enabled,
                "email_address": config.email_address,
                "webhook_enabled": config.webhook_enabled,
                "webhook_url": config.webhook_url,
                "forward_all": config.forward_all,
                "is_active": config.is_active
            }
        }

    except Exception as e:
        logger.error(f"Failed to configure forwarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_forwarding_config(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get forwarding configuration."""
    try:
        config = db.query(ForwardingConfig).filter(
            ForwardingConfig.user_id == user_id
        ).first()

        if not config:
            return {
                "success": True,
                "configured": False,
                "message": "No forwarding configured"
            }

        return {
            "success": True,
            "configured": True,
            "config": {
                "email_enabled": config.email_enabled,
                "email_address": config.email_address,
                "webhook_enabled": config.webhook_enabled,
                "webhook_url": config.webhook_url,
                "forward_all": config.forward_all,
                "is_active": config.is_active
            }
        }

    except Exception as e:
        logger.error(f"Failed to get forwarding config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_forwarding(
    test_message: str = "Test SMS forwarding",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Test forwarding configuration."""
    try:
        config = db.query(ForwardingConfig).filter(
            ForwardingConfig.user_id == user_id
        ).first()

        if not config or not config.is_active:
            raise HTTPException(status_code=400, detail="Forwarding not configured")

        results = []

        # Test email
        if config.email_enabled and config.email_address:
            # TODO: Implement actual email sending
            results.append({
                "type": "email",
                "success": True,
                "message": f"Test email would be sent to {config.email_address}"
            })

        # Test webhook
        if config.webhook_enabled and config.webhook_url:
            # TODO: Implement actual webhook posting
            results.append({
                "type": "webhook",
                "success": True,
                "message": f"Test webhook would be posted to {config.webhook_url}"
            })

        return {
            "success": True,
            "message": "Forwarding test completed",
            "results": results
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Failed to test forwarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
