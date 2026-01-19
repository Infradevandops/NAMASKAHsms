"""API key service with tier enforcement."""

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.core.tier_config_simple import TIER_CONFIG
from app.models.api_key import APIKey
from app.models.user import User
from app.utils.security import generate_api_key


class APIKeyService:
    """Manage API keys with tier-based limits."""

    @staticmethod
    def can_create_key(db: Session, user_id: str) -> bool:
        """Check if user can create API key based on tier."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        tier = TIER_CONFIG.get(user.subscription_tier, {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
            return False

        if limit == -1:
            return True

        current_count = (
            db.query(APIKey)
            .filter(APIKey.user_id == user_id, APIKey.is_active.is_(True))
            .count()
        )

        return current_count < limit

    @staticmethod
    def get_remaining_keys(db: Session, user_id: str) -> int:
        """Get remaining API key slots for user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0

        tier = TIER_CONFIG.get(user.subscription_tier, {})
        limit = tier.get("api_key_limit", 0)

        if limit == 0:
            return 0

        if limit == -1:
            return 999

        current_count = (
            db.query(APIKey)
            .filter(APIKey.user_id == user_id, APIKey.is_active.is_(True))
            .count()
        )

        return max(0, limit - current_count)

    @staticmethod
    def create_key(db: Session, user_id: str, name: str = None) -> dict:
        """Create new API key if allowed."""
        if not APIKeyService.can_create_key(db, user_id):
            raise ValueError("API key limit reached for your tier")

        raw_key = f"sk_{generate_api_key(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_preview = raw_key[-4:]

        key = APIKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key_hash=key_hash,
            key_preview=key_preview,
            name=name
            or f"Key {len(db.query(APIKey).filter(APIKey.user_id == user_id).all()) + 1}",
            is_active=True,
        )
        db.add(key)
        db.commit()

        return {
            "id": key.id,
            "key": raw_key,
            "name": key.name,
            "created_at": key.created_at,
        }
