"""API Key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.tier_manager import TierManager
from app.services.api_key_service import APIKeyService
from app.schemas.tier import APIKeyCreate, APIKeyResponse, APIKeyInfo
from app.models.api_key import APIKey

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


@router.get("/", response_model=list[APIKeyInfo])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user."""
    # Check tier access
    tier_manager = TierManager(db)
    if not tier_manager.check_feature_access(user_id, "api_access"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="API key access requires Starter tier or higher. Please upgrade."
        )
    
    api_key_service = APIKeyService(db)
    keys = api_key_service.get_user_keys(user_id, include_inactive=False)
    
    return [
        APIKeyInfo(
            id=key.id,
            name=key.name,
            key_preview=key.key_preview,
            is_active=key.is_active,
            request_count=key.request_count,
            last_used=key.last_used,
            created_at=key.created_at,
            expires_at=key.expires_at
        )
        for key in keys
    ]


@router.post("/generate", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_api_key(
    key_create: APIKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate a new API key."""
    tier_manager = TierManager(db)
    
    # Check feature access
    if not tier_manager.check_feature_access(user_id, "api_access"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="API key access requires Starter tier or higher. Please upgrade to Starter ($9/mo) or Turbo ($13.99/mo)."
        )
    
    # Check API key limit
    can_create, error_msg = tier_manager.can_create_api_key(user_id)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )
    
    # Generate the key
    api_key_service = APIKeyService(db)
    plain_key, api_key_model = api_key_service.generate_api_key(user_id, key_create.name)
    
    return APIKeyResponse(
        id=api_key_model.id,
        name=api_key_model.name,
        key=plain_key,  # Only shown once!
        key_preview=api_key_model.key_preview,
        created_at=api_key_model.created_at,
        expires_at=api_key_model.expires_at
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Revoke (delete) an API key."""
    api_key_service = APIKeyService(db)
    success = api_key_service.revoke_api_key(key_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "message": "API key revoked successfully"}


@router.post("/{key_id}/rotate", response_model=APIKeyResponse)
async def rotate_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
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
        created_at=new_key.created_at,
        expires_at=new_key.expires_at
    )


@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get usage statistics for an API key."""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user_id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {
        "key_id": api_key.id,
        "name": api_key.name,
        "total_requests": api_key.request_count,
        "last_used": api_key.last_used,
        "created_at": api_key.created_at,
        "is_active": api_key.is_active
    }
