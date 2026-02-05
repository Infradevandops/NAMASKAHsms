"""Authentication service for user login and token management."""

import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


class AuthService:
    """Authentication service for user management."""

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
                "sub": user.id,
                "email": user.email,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            }
            
            token = jwt.encode(
                payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm
            )
            
            print(f"[AUTH] Token created for user {user.id}, expires: {expire}")
            return token
            
        except Exception as e:
            print(f"[AUTH] Token creation failed: {e}")
            traceback.print_exc()
            raise

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                print("[AUTH] No user ID in token")
                return None
                
            # Verify user still exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"[AUTH] User {user_id} not found")
                return None
                
            return user_id
            
        except jwt.ExpiredSignatureError:
            print("[AUTH] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[AUTH] Invalid token: {e}")
            return None
        except Exception as e:
            print(f"[AUTH] Token verification error: {e}")
            return None

    def create_user(self, email: str, password: str, **kwargs) -> User:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")

            # Create new user
            password_hash = get_password_hash(password)
            user = User(
                email=email,
                password_hash=password_hash,
                **kwargs
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            print(f"[AUTH] User created: {user.id}")
            return user
            
        except Exception as e:
            self.db.rollback()
            print(f"[AUTH] User creation failed: {e}")
            raise

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            user.password_hash = get_password_hash(new_password)
            self.db.commit()
            
            print(f"[AUTH] Password updated for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"[AUTH] Password update failed: {e}")
            return False