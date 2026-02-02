"""Authentication service for user login and token management."""

import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import User
from app.utils.security import verify_password, get_password_hash
import jwt

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            print(f"[AUTH] Querying user: {email}")
            user = self.db.query(User).filter(User.email == email).first()
            print(f"[AUTH] User found: {user is not None}")
            
            if not user:
                print("[AUTH] User not found")
                return None

            # Handle users without password hash (OAuth users)
            if not user.password_hash:
                print("[AUTH] No password hash")
                return None

            # Verify password with proper error handling
            print(f"[AUTH] Verifying password, hash starts with: {user.password_hash[:30]}")
            verified = verify_password(password, user.password_hash)
            print(f"[AUTH] Password verified: {verified}")
            
            if not verified:
                print("[AUTH] Password verification failed")
                return None

            print("[AUTH] Authentication successful")
            return user
            
        except Exception as e:
            # Log authentication error but don't expose details
            print(f"[AUTH] Exception: {e}")
            traceback.print_exc()
            return None

    def create_user_token(self, user: User, expires_hours: int = 24 * 30) -> str:
        """Create JWT token for user."""
        try:
            expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            payload = {
                "sub": str(user.id),
                "email": user.email,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            }
            
            token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
            return token
            
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user from JWT token."""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: str, password: str, **kwargs) -> User:
        """Create a new user with hashed password."""
        password_hash = get_password_hash(password)
        
        user = User(
            email=email,
            password_hash=password_hash,
            **kwargs
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.password_hash = get_password_hash(new_password)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Password update failed: {e}")
            return False