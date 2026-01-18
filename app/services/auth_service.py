"""Authentication service for user management and JWT operations."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


from app.core.config import get_settings
from app.models.user import User
from app.models.api_key import APIKey
from app.core.exceptions import AuthenticationError, ValidationError
from app.utils.security import (
    create_access_token,
    generate_api_key,
    generate_secure_id,
    hash_password,
    verify_password,
    verify_token,
)
from app.services.base import BaseService


class AuthService(BaseService[User]):
    """Authentication service for user operations."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def register_user(self, email: str, password: str, referral_code: Optional[str] = None) -> User:
        """Register a new user account."""
        # Check if user exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValidationError("Email already registered")

        # Create user
        user_data = {
            "email": email,
            "password_hash": hash_password(password),
            "referral_code": generate_secure_id("ref", 6),
        }

        # Handle referral
        if referral_code:
            referrer = self.db.query(User).filter(User.referral_code == referral_code).first()
            if referrer:
                user_data["referred_by"] = referrer.id
                user_data["free_verifications"] = 2.0  # Bonus for being referred

        return self.create(**user_data)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            print(f"[AUTH] Querying user: {email}")
            user = self.db.query(User).filter(User.email == email).first()
            print(f"[AUTH] User found: {user is not None}")
            if not user:
                print(f"[AUTH] User not found")
                return None

            # Handle users without password hash (OAuth users)
            if not user.password_hash:
                print(f"[AUTH] No password hash")
                return None

            # Verify password with proper error handling
            print(f"[AUTH] Verifying password, hash starts with: {user.password_hash[:30]}")
            verified = verify_password(password, user.password_hash)
            print(f"[AUTH] Password verified: {verified}")
            if not verified:
                print(f"[AUTH] Password verification failed")
                return None

            print(f"[AUTH] Authentication successful")
            return user
        except Exception as e:
            # Log authentication error but don't expose details
            print(f"[AUTH] Exception: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def create_user_token(user: User, expires_hours: int = 24 * 30) -> str:
        """Create JWT token for user."""
        data = {"user_id": user.id, "email": user.email}
        expires_delta = timedelta(hours=expires_hours)
        return create_access_token(data, expires_delta)

    @staticmethod
    def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        return verify_token(token)

    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token."""
        payload = self.verify_user_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        return self.get_by_id(user_id)

    def create_api_key(self, user_id: str, name: str) -> APIKey:
        """Create API key for user."""
        raw_key = f"nsk_{generate_api_key()}"
        hashed_key = hash_password(raw_key)
        key_preview = f"...{raw_key[-6:]}"  # Last 6 chars for display
        api_key = APIKey(user_id=user_id, key_hash=hashed_key, key_preview=key_preview, name=name)
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        # Return object with raw key for display (only shown once)
        api_key.raw_key = raw_key
        return api_key

    def verify_api_key(self, key: str) -> Optional[User]:
        """Verify API key and return associated user."""
        api_keys = self.db.query(APIKey).filter(APIKey.is_active.is_(True)).all()

        for api_key in api_keys:
            if verify_password(key, api_key.key_hash):
                return self.get_by_id(api_key.user_id)

        return None

    def deactivate_api_key(self, key_id: str, user_id: str) -> bool:
        """Deactivate API key for user."""
        api_key = (
            self.db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
        )

        if not api_key:
            return False

        self.db.delete(api_key)
        self.db.commit()
        return True

    def get_user_api_keys(self, user_id: str) -> list[APIKey]:
        """Get all API keys for user."""
        return self.db.query(APIKey).filter(APIKey.user_id == user_id).all()

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        user.password_hash = hash_password(new_password)
        user.update_timestamp()
        self.db.commit()
        return True

    def verify_admin_access(self, user_id: str) -> bool:
        """Verify user has admin access."""
        user = self.get_by_id(user_id)
        return user is not None and user.is_admin

    def create_or_get_google_user(
        self, google_id: str, email: str, name: str = None, avatar_url: str = None
    ) -> User:
        """Create or get user from Google OAuth."""
        # Check if user exists by Google ID
        user = self.db.query(User).filter(User.google_id == google_id).first()
        if user:
            return user

        # Check if user exists by email
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            user.provider = "google"
            user.email_verified = True
            if avatar_url:
                user.avatar_url = avatar_url
            self.db.commit()
            return user

        # Create new Google user
        user_data = {
            "email": email,
            "google_id": google_id,
            "provider": "google",
            "email_verified": True,
            "referral_code": generate_secure_id("re", 6),
            "free_verifications": 2.0,  # Bonus for Google signup
        }

        if avatar_url:
            user_data["avatar_url"] = avatar_url

        return self.create(**user_data)

    def reset_password_request(self, email: str) -> Optional[str]:
        """Generate password reset token for user."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None

        # Generate reset token
        reset_token = generate_secure_id("rst", 32)

        # Set token and expiry (1 hour)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        self.db.commit()
        return reset_token

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token."""
        user = self.db.query(User).filter(User.reset_token == token).first()

        if not user or not user.reset_token_expires:
            return False

        # Check if token is expired
        now = datetime.now(timezone.utc)
        expires = user.reset_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
            
        if now > expires:
            return False

        # Update password and clear reset token
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None

        self.db.commit()
        return True

    def verify_email(self, token: str) -> bool:
        """Verify email using verification token."""
        user = self.db.query(User).filter(User.verification_token == token).first()

        if not user:
            return False

        user.email_verified = True
        user.verification_token = None

        self.db.commit()
        return True


def get_auth_service(db: Session) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)
