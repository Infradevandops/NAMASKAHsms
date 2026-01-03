"""Pytest configuration and fixtures for tests."""
import pytest
import sys
import jwt
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.subscription_tier import SubscriptionTier
from app.models.user_quota import UserQuota
from app.utils.security import hash_password
import main


# Create test database engine
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_token(user_id: str, email: str = "test@test.com") -> str:
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    # Populate subscription tiers
    from app.models.subscription_tier import SubscriptionTier
    
    tiers_data = [
        {
            "id": "tier_freemium",
            "tier": "freemium",
            "name": "Freemium",
            "description": "Free tier with basic features",
            "price_monthly": 0,
            "payment_required": False,
            "quota_usd": 0.0,
            "overage_rate": 0.0,
            "has_api_access": False,
            "has_area_code_selection": False,
            "has_isp_filtering": False,
            "api_key_limit": 0,
            "support_level": "community"
        },
        {
            "id": "tier_payg",
            "tier": "payg",
            "name": "Pay-As-You-Go",
            "description": "Pay as you go tier",
            "price_monthly": 0,
            "payment_required": True,
            "quota_usd": 100.0,
            "overage_rate": 0.05,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": False,
            "api_key_limit": 5,
            "support_level": "email"
        },
        {
            "id": "tier_pro",
            "tier": "pro",
            "name": "Pro",
            "description": "Professional tier",
            "price_monthly": 9900,
            "payment_required": True,
            "quota_usd": 500.0,
            "overage_rate": 0.03,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": 20,
            "support_level": "priority"
        },
        {
            "id": "tier_custom",
            "tier": "custom",
            "name": "Custom",
            "description": "Custom enterprise tier",
            "price_monthly": 0,
            "payment_required": True,
            "quota_usd": 10000.0,
            "overage_rate": 0.01,
            "has_api_access": True,
            "has_area_code_selection": True,
            "has_isp_filtering": True,
            "api_key_limit": -1,
            "support_level": "priority"
        }
    ]
    
    for tier_data in tiers_data:
        tier = SubscriptionTier(**tier_data)
        session.add(tier)
    
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Override the dependency
    main.app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(main.app) as test_client:
        yield test_client
    
    # Clear overrides after test
    main.app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    """Create admin token fixture factory."""
    def _create_token(user_id: str, email: str = "admin@test.com"):
        return create_test_token(user_id, email)
    return _create_token


@pytest.fixture
def user_token():
    """Create user token fixture factory."""
    def _create_token(user_id: str, email: str = "user@test.com"):
        return create_test_token(user_id, email)
    return _create_token


@pytest.fixture
def regular_user(db: Session):
    """Create a regular user in the database."""
    user = User(
        id="user_123",
        email="user@test.com",
        password_hash=hash_password("password123"),
        email_verified=True,
        is_admin=False,
        credits=10.0,
        free_verifications=1.0,
        subscription_tier="freemium",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user in the database."""
    user = User(
        id="admin_123",
        email="admin@test.com",
        password_hash=hash_password("adminpass123"),
        email_verified=True,
        is_admin=True,
        credits=100.0,
        free_verifications=10.0,
        subscription_tier="turbo",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    return user
