"""API key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from app.core.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/keys", tags=["api-keys"])


@router.post("/generate")
async def generate_api_key(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate new API key."""
    try:
        # Generate secure random key
        key = f"sk_{secrets.token_urlsafe(32)}"

        api_key = APIKey(
            user_id=user_id,
            key=key,
            name=f"API Key {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            is_active=True,
        )
        db.add(api_key)
        db.commit()

        return {
            "success": True,
            "id": api_key.id,
            "key": key,
            "name": api_key.name,
            "created_at": api_key.created_at.isoformat(),
            "message": "Save this key securely - you won't see it again",
        }

    except Exception as e:
        logger.error(f"Generate API key error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


@router.get("/list")
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List user's API keys."""
    try:
        keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()

        return {
            "success": True,
            "keys": [
                {
                    "id": k.id,
                    "name": k.name,
                    "key_preview": f"{k.key[:10]}...{k.key[-4:]}",
                    "is_active": k.is_active,
                    "created_at": k.created_at.isoformat(),
                    "last_used": k.last_used.isoformat() if k.last_used else None,
                }
                for k in keys
            ],
            "total": len(keys),
        }

    except Exception as e:
        logger.error(f"List API keys error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Revoke API key."""
    try:
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id, APIKey.user_id == user_id
        ).first()

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        api_key.is_active = False
        db.commit()

        return {
            "success": True,
            "message": "API key revoked",
        }

    except HTTPException:
        pass
    except Exception as e:
        logger.error(f"Revoke API key error: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.get("/usage")
async def get_api_usage(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get API usage statistics."""
    try:
        keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()

        total_requests = sum(k.request_count or 0 for k in keys)
        active_keys = sum(1 for k in keys if k.is_active)

        return {
            "success": True,
            "total_requests": total_requests,
            "active_keys": active_keys,
            "total_keys": len(keys),
            "keys": [
                {
                    "name": k.name,
                    "requests": k.request_count or 0,
                    "last_used": k.last_used.isoformat() if k.last_used else None,
                }
                for k in keys
            ],
        }

    except Exception as e:
        logger.error(f"Get API usage error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API usage")
