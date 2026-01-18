"""API key service with tier enforcement."""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.api_key import APIKey
from app.core.tier_config_simple import TIER_CONFIG
import uuid


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
            db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.is_active == True).count()
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
            db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.is_active == True).count()
        )

        return max(0, limit - current_count)

    @staticmethod
    def create_key(db: Session, user_id: str, name: str = None) -> dict:
        """Create new API key if allowed."""
        if not APIKeyService.can_create_key(db, user_id):
            raise ValueError("API key limit reached for your tier")

        key = APIKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key=str(uuid.uuid4()),
            name=name or f"Key {len(db.query(APIKey).filter(APIKey.user_id == user_id).all()) + 1}",
            is_active=True,
        )
        db.add(key)
        db.commit()

        return {"id": key.id, "key": key.key, "name": key.name, "created_at": key.created_at}
