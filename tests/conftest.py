import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone
import jwt
import time

from app.core.database import Base, get_db
from main import app
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.core.config import get_settings

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

settings = get_settings()

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed Data: Subscription Tiers
    seed_tiers(session)
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with a database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def seed_tiers(session):
    """Seed the database with default subscription tiers."""
    tiers = [
        SubscriptionTier(
            tier="freemium",
            name="Freemium",
            description="Starter plan",
            price_monthly=0,
            payment_required=False,
            has_api_access=False,
            api_key_limit=0,
            rate_limit_per_minute=5
        ),
        SubscriptionTier(
            tier="pro",
            name="Pro",
            description="Professional plan",
            price_monthly=2500,
            payment_required=True,
            has_api_access=True,
            api_key_limit=10,
            rate_limit_per_minute=60
        ),
         SubscriptionTier(
            tier="payg",
            name="Pay As You Go",
            description="Pay As You Go plan",
            price_monthly=0,
            payment_required=False,
            has_api_access=False,
            api_key_limit=0,
            rate_limit_per_minute=5
        )
    ]
    for tier in tiers:
        # Check if exists to avoid duplication if we move scope to module/session later
        existing = session.query(SubscriptionTier).filter_by(tier=tier.tier).first()
        if not existing:
            session.add(tier)
    session.commit()

@pytest.fixture(scope="function")
def regular_user(db_session):
    """Create a regular user."""
    user = User(
        email="user@example.com",
        password_hash="hashedpassword",
        subscription_tier="freemium",
        email_verified=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        password_hash="hashedpassword",
        subscription_tier="pro",
        email_verified=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def user_token(regular_user):
    """Create a valid access token for a regular user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": str(regular_user.id),
        "user_id": str(regular_user.id),
        "email": regular_user.email,
        "is_admin": False,
        "exp": expire
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@pytest.fixture(scope="function")
def admin_token(admin_user):
    """Create a valid access token for an admin user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": str(admin_user.id),
        "user_id": str(admin_user.id),
        "email": admin_user.email,
        "is_admin": True,
        "exp": expire
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@pytest.fixture(scope="function")
def client_authenticated(client, user_token):
    """TestClient authenticated as regular user."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {user_token}",
    }
    return client

@pytest.fixture(scope="function")
def admin_client(client, admin_token):
    """TestClient authenticated as admin."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {admin_token}",
    }
    return client

def create_test_token(user_id: str, email: str, is_admin: bool = False, expires_minutes: int = 15) -> str:
    """
    Helper function to create test JWT tokens.
    Used by test files that need to generate custom tokens.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "exp": expire
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@pytest.fixture
def freemium_user(db_session):
    user = User(email="free@test.com", subscription_tier="freemium", password_hash="test", is_admin=False, free_verifications=1.0)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def payg_user(db_session):
    user = User(email="payg@test.com", subscription_tier="payg", password_hash="test", is_admin=False, free_verifications=1.0)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def pro_user(db_session):
    user = User(email="pro@test.com", subscription_tier="pro", password_hash="test", is_admin=False, free_verifications=1.0)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_header():
    def _auth_header(user):
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "exp": expire
        }
        token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return {"Authorization": f"Bearer {token}"}
    return _auth_header
