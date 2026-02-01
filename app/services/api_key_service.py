"""API key service with tier enforcement."""


import hashlib
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.core.tier_config_simple import TIER_CONFIG
from app.models.api_key import APIKey
from app.models.user import User
from app.utils.security import generate_api_key

class APIKeyService:

    """Manage API keys with tier-based limits."""

    def __init__(self, db: Session):

        self.db = db

    def can_create_key(self, user_id: str) -> bool:

        """Check if user can create API key based on tier."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
        return False

        tier = TIER_CONFIG.get(user.subscription_tier, {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
        return False

        if limit == -1:
        return True

        current_count = self.db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.is_active.is_(True)).count()

        return current_count < limit

    def get_remaining_keys(self, user_id: str) -> int:

        """Get remaining API key slots for user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
        return 0

        tier = TIER_CONFIG.get(user.subscription_tier, {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
        return 0

        if limit == -1:
        return 999

        current_count = self.db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.is_active.is_(True)).count()

        return max(0, limit - current_count)

    def generate_api_key(self, user_id: str, name: str = None) -> tuple[str, APIKey]:

        """Generate a new API key."""
        if not self.can_create_key(user_id):
            raise ValueError("API key limit reached for your tier")

        raw_key = f"sk_{generate_api_key(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_preview = raw_key[-4:]

        api_key = APIKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key_hash=key_hash,
            key_preview=key_preview,
            name=name or f"Key {len(self.db.query(APIKey).filter(APIKey.user_id == user_id).all()) + 1}",
            is_active=True,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return raw_key, api_key

    def get_user_keys(self, user_id: str, include_inactive: bool = False) -> list[APIKey]:

        """Get all API keys for a user."""
        query = self.db.query(APIKey).filter(APIKey.user_id == user_id)
        if not include_inactive:
            query = query.filter(APIKey.is_active.is_(True))
        return query.all()

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:

        """Revoke an API key."""
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
        if not api_key:
        return False

        api_key.is_active = False
        self.db.commit()
        return True

    def rotate_api_key(self, key_id: str, user_id: str) -> Optional[tuple[str, APIKey]]:

        """Rotate an API key."""
        if not self.revoke_api_key(key_id, user_id):
        return None
        return self.generate_api_key(user_id)
