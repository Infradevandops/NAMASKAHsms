"""Authentication service for user login and token management."""

import traceback
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_redis():
    from app.core.cache import get_redis

    return get_redis()


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
            logger.debug("Querying user by email")
            user = self.db.query(User).filter(User.email == email).first()
            logger.debug("User lookup complete", extra={"found": user is not None})

            if not user:
                return None

            if not user.password_hash:
                return None

            verified = verify_password(password, user.password_hash)

            if not verified:
                return None

            return user

        except Exception as e:
            logger.error("Authentication error", extra={"error": str(e)})
            traceback.print_exc()
            return None

    def create_user_token(self, user: User, expires_hours: Optional[int] = None) -> str:
        """Create JWT token for user."""
        try:
            hours = (
                expires_hours
                if expires_hours is not None
                else settings.jwt_expiration_hours
            )
            expire = datetime.now(timezone.utc) + timedelta(hours=hours)
            jti = str(uuid.uuid4())
            payload = {
                "sub": user.id,
                "email": user.email,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access",
                "jti": jti,
            }

            token = jwt.encode(
                payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
            )

            logger.debug("Token created", extra={"user_id": str(user.id)})
            return token

        except Exception as e:
            logger.error("Token creation failed", extra={"error": str(e)})
            traceback.print_exc()
            raise

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )

            # Check token blacklist (logout revocation)
            jti = payload.get("jti")
            if jti:
                try:
                    redis = _get_redis()
                    if redis.exists(f"blacklist:jti:{jti}"):
                        logger.debug("Token revoked", extra={"jti": jti})
                        return None
                except Exception as e:
                    logger.warning(f"Blacklist check failed (allowing token): {e}")

            # Support both 'sub' and 'user_id' for backwards compatibility
            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                return None

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            return user_id

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError as e:
            logger.debug("Invalid token", extra={"error": str(e)})
            return None
        except Exception as e:
            logger.error("Token verification error", extra={"error": str(e)})
            return None

    def revoke_token(self, token: str) -> bool:
        """Blacklist a JWT token so it cannot be used after logout."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if not jti:
                return False
            ttl = (
                max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
                if exp
                else 86400
            )
            redis = _get_redis()
            redis.setex(f"blacklist:jti:{jti}", ttl, "1")
            logger.info("Token revoked", extra={"jti": jti})
            return True
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False

    def create_user(self, email: str, password: str, **kwargs) -> User:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")

            # Create new user
            password_hash = get_password_hash(password)
            user = User(email=email, password_hash=password_hash, **kwargs)

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info("User created", extra={"user_id": str(user.id)})
            return user

        except Exception as e:
            self.db.rollback()
            logger.error("User creation failed", extra={"error": str(e)})
            raise

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.password_hash = get_password_hash(new_password)
            self.db.commit()

            logger.info("Password updated", extra={"user_id": user_id})
            return True

        except Exception as e:
            self.db.rollback()
            logger.error("Password update failed", extra={"error": str(e)})
            return False
