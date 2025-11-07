"""Tests for authentication service."""
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User, APIKey
from app.services.auth_service import AuthService, get_auth_service
from app.core.exceptions import ValidationError


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def auth_service(db_session):
    """Create authentication service instance."""
    return AuthService(db_session)


def test_register_user(auth_service):
    """Test user registration."""
    user = auth_service.register_user("test@example.com", "password123")
    
    assert user is not None
    assert user.email == "test@example.com"
    assert user.password_hash != "password123"  # Should be hashed
    assert user.referral_code is not None
    assert user.free_verifications == 1.0


def test_register_user_with_referral(auth_service):
    """Test user registration with referral code."""
    # Create referrer
    referrer = auth_service.register_user("referrer@example.com", "password123")
    
    # Register with referral
    user = auth_service.register_user("referred@example.com", "password123", referrer.referral_code)
    
    assert user.referred_by == referrer.id
    assert user.free_verifications == 2.0  # Bonus for being referred


def test_register_duplicate_email(auth_service):
    """Test registration with duplicate email."""
    auth_service.register_user("test@example.com", "password123")
    
    with pytest.raises(ValidationError, match="Email already registered"):
        auth_service.register_user("test@example.com", "password456")


def test_authenticate_user_success(auth_service):
    """Test successful user authentication."""
    # Register user
    registered = auth_service.register_user("test@example.com", "password123")
    
    # Authenticate
    user = auth_service.authenticate_user("test@example.com", "password123")
    
    assert user is not None
    assert user.id == registered.id
    assert user.email == "test@example.com"


def test_authenticate_user_wrong_password(auth_service):
    """Test authentication with wrong password."""
    auth_service.register_user("test@example.com", "password123")
    
    user = auth_service.authenticate_user("test@example.com", "wrongpassword")
    
    assert user is None


def test_authenticate_user_not_found(auth_service):
    """Test authentication with non-existent user."""
    user = auth_service.authenticate_user("nonexistent@example.com", "password123")
    
    assert user is None


def test_create_user_token(auth_service):
    """Test JWT token creation."""
    user = auth_service.register_user("test@example.com", "password123")
    
    token = auth_service.create_user_token(user)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_user_token(auth_service):
    """Test JWT token verification."""
    user = auth_service.register_user("test@example.com", "password123")
    token = auth_service.create_user_token(user)
    
    payload = auth_service.verify_user_token(token)
    
    assert payload is not None
    assert payload["user_id"] == user.id
    assert payload["email"] == user.email


def test_get_user_from_token(auth_service):
    """Test getting user from JWT token."""
    user = auth_service.register_user("test@example.com", "password123")
    token = auth_service.create_user_token(user)
    
    retrieved_user = auth_service.get_user_from_token(token)
    
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


def test_create_api_key(auth_service):
    """Test API key creation."""
    user = auth_service.register_user("test@example.com", "password123")
    
    api_key = auth_service.create_api_key(user.id, "Test Key")
    
    assert api_key is not None
    assert api_key.user_id == user.id
    assert api_key.name == "Test Key"
    assert api_key.key.startswith("nsk_")
    assert api_key.is_active is True


def test_verify_api_key(auth_service):
    """Test API key verification."""
    user = auth_service.register_user("test@example.com", "password123")
    api_key = auth_service.create_api_key(user.id, "Test Key")
    
    verified_user = auth_service.verify_api_key(api_key.key)
    
    assert verified_user is not None
    assert verified_user.id == user.id


def test_verify_invalid_api_key(auth_service):
    """Test verification of invalid API key."""
    user = auth_service.verify_api_key("invalid_key")
    
    assert user is None


def test_deactivate_api_key(auth_service):
    """Test API key deactivation."""
    user = auth_service.register_user("test@example.com", "password123")
    api_key = auth_service.create_api_key(user.id, "Test Key")
    
    success = auth_service.deactivate_api_key(api_key.id, user.id)
    
    assert success is True
    
    # Verify key is deactivated
    verified_user = auth_service.verify_api_key(api_key.key)
    assert verified_user is None


def test_get_user_api_keys(auth_service):
    """Test getting user API keys."""
    user = auth_service.register_user("test@example.com", "password123")
    auth_service.create_api_key(user.id, "Key 1")
    auth_service.create_api_key(user.id, "Key 2")
    
    api_keys = auth_service.get_user_api_keys(user.id)
    
    assert len(api_keys) == 2
    assert all(key.user_id == user.id for key in api_keys)


def test_update_password(auth_service):
    """Test password update."""
    user = auth_service.register_user("test@example.com", "password123")
    
    success = auth_service.update_password(user.id, "newpassword456")
    
    assert success is True
    
    # Verify old password doesn't work
    old_auth = auth_service.authenticate_user("test@example.com", "password123")
    assert old_auth is None
    
    # Verify new password works
    new_auth = auth_service.authenticate_user("test@example.com", "newpassword456")
    assert new_auth is not None


def test_verify_admin_access(auth_service):
    """Test admin access verification."""
    # Regular user
    user = auth_service.register_user("test@example.com", "password123")
    assert auth_service.verify_admin_access(user.id) is False
    
    # Admin user
    user.is_admin = True
    auth_service.db.commit()
    assert auth_service.verify_admin_access(user.id) is True


def test_auth_service_factory(db_session):
    """Test authentication service factory."""
    service = get_auth_service(db_session)
    
    assert isinstance(service, AuthService)
    assert service.db == db_session


if __name__ == "__main__":
    pytest.main([__file__])