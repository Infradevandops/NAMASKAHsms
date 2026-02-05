"""API Key management service."""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.api_key import APIKey
from app.models.user import User
from app.core.tier_config import TierConfig

# Tier configuration for API key limits
TIER_CONFIG = {
    "freemium": {"api_key_limit": 0},
    "payg": {"api_key_limit": 0},
    "pro": {"api_key_limit": 10},
    "custom": {"api_key_limit": -1},  # Unlimited
}


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, db: Session):
        self.db = db

    def can_create_key(self, user_id: str) -> bool:
        """Check if user can create API key based on tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
        return False

        tier = TIER_CONFIG.get(user.tier or "freemium", {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
        return False

        if limit == -1:
        return True

        current_count = self.db.query(APIKey).filter(
            APIKey.user_id == user_id, 
            APIKey.is_active.is_(True)
        ).count()

        return current_count < limit

    def get_remaining_keys(self, user_id: str) -> int:
        """Get remaining API key slots for user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
        return 0

        tier = TIER_CONFIG.get(user.tier or "freemium", {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
        return 0

        if limit == -1:
        return 999  # Unlimited

        current_count = self.db.query(APIKey).filter(
            APIKey.user_id == user_id, 
            APIKey.is_active.is_(True)
        ).count()

        return max(0, limit - current_count)

    def generate_api_key(self, user_id: str, name: str) -> Tuple[str, APIKey]:
        """Generate a new API key for user."""
        # Generate secure key
        plain_key = f"nsk_{secrets.token_urlsafe(32)}"
        
        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=plain_key,  # In production, this should be hashed
            key_preview=f"{plain_key[:8]}...{plain_key[-4:]}",
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            request_count=0
        )

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return plain_key, api_key

    def get_user_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for user."""
        return self.db.query(APIKey).filter(
            APIKey.user_id == user_id
        ).order_by(APIKey.created_at.desc()).all()

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key."""
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()

        if not api_key:
        return False

        api_key.is_active = False
        self.db.commit()
        return True

    def rotate_api_key(self, key_id: str, user_id: str) -> Optional[Tuple[str, APIKey]]:
        """Rotate an API key (generate new key, deactivate old)."""
        old_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()

        if not old_key:
        return None

        # Generate new key
        plain_key, new_key = self.generate_api_key(user_id, old_key.name)

        # Deactivate old key
        old_key.is_active = False
        self.db.commit()

        return plain_key, new_key

    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key and return the associated record."""
        api_key = self.db.query(APIKey).filter(
            APIKey.key_hash == key,
            APIKey.is_active.is_(True)
        ).first()

        if api_key and api_key.expires_at > datetime.utcnow():
            # Update last used timestamp
            api_key.last_used = datetime.utcnow()
            api_key.request_count += 1
            self.db.commit()
        return api_key

        return None
