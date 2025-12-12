"""API Key management service."""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.api_key import APIKey
from app.models.user import User


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_api_key(self, user_id: str,
                             name: str, expires_days: int = 365) -> dict:
        """Create new API key."""
        # Generate key
        key = f"nsk_{secrets.token_urlsafe(32)}"
        prefix = key[:8]
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        # Create record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )

        self.db.add(api_key)
        await self.db.commit()

        return {"key": key, "prefix": prefix, "expires_at": api_key.expires_at}

    async def verify_api_key(self, key: str) -> User:
        """Verify API key and return user."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        query = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active,
            APIKey.expires_at > datetime.utcnow()
        )
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Update last used
        api_key.last_used = datetime.utcnow()
        await self.db.commit()

        # Get user
        user_query = select(User).where(User.id == api_key.user_id)
        user_result = await self.db.execute(user_query)
        return user_result.scalar_one_or_none()
