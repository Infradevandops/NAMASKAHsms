"""API Key management endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id, require_tier
from app.models.api_key import APIKey
from app.schemas.auth import APIKeyCreate, APIKeyListResponse, APIKeyResponse
from app.services.api_key_service import APIKeyService
from app.services.tier_manager import TierManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keys", tags=["API Keys"])

# Tier dependency for payg+ access
require_payg = require_tier("payg")


@router.get("/", response_model=list[APIKeyListResponse])
async def list_api_keys(user_id: str = Depends(require_payg), db: Session = Depends(get_db)):
    """List all API keys for the current user."""
    logger.info(f"API keys list requested by user_id: {user_id}")

    api_key_service = APIKeyService(db)
    keys = api_key_service.get_user_keys(user_id, include_inactive=False)

    logger.debug(f"Retrieved {len(keys)} API keys for user {user_id}")

    return [
        APIKeyListResponse(
            id=key.id,
            name=key.name,
            key_preview=key.key_preview,
            is_active=key.is_active,
            request_count=key.request_count,
            last_used=key.last_used,
            created_at=key.created_at,
            expires_at=key.expires_at,
        )
        for key in keys
    ]


@router.post("/generate", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_api_key(
    key_create: APIKeyCreate,
    user_id: str = Depends(require_payg),
    db: Session = Depends(get_db),
):
    """Generate a new API key."""
    logger.info(f"API key generation requested by user_id: {user_id}, name: {key_create.name}")

    tier_manager = TierManager(db)

    # Check API key limit
    can_create, error_msg = tier_manager.can_create_api_key(user_id)
    if not can_create:
        logger.warning(f"API key generation denied for user {user_id}: {error_msg}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_msg)

    # Generate the key
    api_key_service = APIKeyService(db)
    plain_key, api_key_model = api_key_service.generate_api_key(user_id, key_create.name)

    logger.info(f"API key generated successfully for user {user_id}, key_id: {api_key_model.id}")

    return APIKeyResponse(
        id=api_key_model.id,
        name=api_key_model.name,
        key=plain_key,  # Only shown once!
        key_preview=api_key_model.key_preview,
        is_active=api_key_model.is_active,
        created_at=api_key_model.created_at,
        expires_at=api_key_model.expires_at,
        last_used=api_key_model.last_used,
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Revoke (delete) an API key."""
    logger.info(f"API key revocation requested by user_id: {user_id}, key_id: {key_id}")

    api_key_service = APIKeyService(db)
    success = api_key_service.revoke_api_key(key_id, user_id)

    if not success:
        logger.warning(f"API key revocation failed - key not found: user_id={user_id}, key_id={key_id}")
        raise HTTPException(status_code=404, detail="API key not found")

    logger.info(f"API key revoked successfully: user_id={user_id}, key_id={key_id}")
    return {"success": True, "message": "API key revoked successfully"}


@router.post("/{key_id}/rotate", response_model=APIKeyResponse)
async def rotate_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Rotate an API key (revoke old, create new)."""
    api_key_service = APIKeyService(db)
    result = api_key_service.rotate_api_key(key_id, user_id)

    if not result:
        raise HTTPException(status_code=404, detail="API key not found")

    plain_key, new_key = result

    return APIKeyResponse(
        id=new_key.id,
        name=new_key.name,
        key=plain_key,  # Only shown once!
        key_preview=new_key.key_preview,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        expires_at=new_key.expires_at,
        last_used=new_key.last_used,
    )


@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get usage statistics for an API key."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "key_id": api_key.id,
        "name": api_key.name,
        "total_requests": api_key.request_count,
        "last_used": api_key.last_used,
        "created_at": api_key.created_at,
        "is_active": api_key.is_active,
    }
