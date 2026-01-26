import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import MagicMock, patch

import fakeredis
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_32_characters_long_enough"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_testing_32_characters_long"

# Mock background services to prevent startup
patch("app.services.sms_polling_service.sms_polling_service.start_background_service").start()
patch("app.services.voice_polling_service.voice_polling_service.start_background_service").start()

# 1. Setup in-memory database engine FIRST
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
mock_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# Prevent engine.dispose from closing the in-memory DB connection during tests
mock_engine.dispose = lambda: None

# 2. Patch global engine references BEFORE importing app
patch("app.core.database.engine", new=mock_engine).start()
patch("app.core.lifespan.engine", new=mock_engine).start()
patch("app.core.startup.engine", new=mock_engine).start()

# Also patch SessionLocal to ensure it uses the mock engine
MockSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mock_engine)
patch("app.core.database.SessionLocal", new=MockSessionLocal).start()

# 3. Patch startup functions to prevent DB initialization logic that might fail
# or try to use Postgres-specific SQL on SQLite
patch("app.core.lifespan.run_startup_initialization").start()
patch("app.core.startup.run_startup_initialization").start()

from app.core.config import settings

# 4. Now safe to import app
from app.core.database import Base, get_db
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.models.user_preference import UserPreference
from app.utils.security import hash_password
from main import app

# 5. Define Session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mock_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    # Create tables in the in-memory DB
    Base.metadata.create_all(bind=mock_engine)
    session = TestingSessionLocal()

    # Seed Data: Subscription Tiers
    seed_tiers(session)

    try:
        yield session
    finally:
        session.close()
        # Drop tables to ensure clean state for next test
        Base.metadata.drop_all(bind=mock_engine)


@pytest.fixture(scope="function")
def db(db_session):
    return db_session


@pytest.fixture(scope="function")
def redis_client():
    """Create a fake Redis client for testing."""
    server = fakeredis.FakeServer()
    redis = fakeredis.FakeRedis(server=server, decode_responses=True)
    return redis


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with a database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # TestClient trigger startup events, but our patches should protect us
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise e
    finally:
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
            rate_limit_per_minute=5,
        ),
        SubscriptionTier(
            tier="pro",
            name="Pro",
            description="Professional plan",
            price_monthly=2500,
            payment_required=True,
            has_api_access=True,
            api_key_limit=10,
            rate_limit_per_minute=60,
        ),
        SubscriptionTier(
            tier="payg",
            name="Pay As You Go",
            description="Pay As You Go plan",
            price_monthly=0,
            payment_required=False,
            has_api_access=True,
            api_key_limit=2,
            rate_limit_per_minute=30,
        ),
        SubscriptionTier(
            tier="custom",
            name="Custom",
            description="Enterprise plan",
            price_monthly=5000,
            payment_required=True,
            has_api_access=True,
            api_key_limit=100,
            rate_limit_per_minute=600,
        ),
    ]
    for tier in tiers:
        existing = session.query(SubscriptionTier).filter_by(tier=tier.tier).first()
        if not existing:
            session.add(tier)
    session.commit()


@pytest.fixture(scope="function")
def regular_user(db_session):
    """Create a regular user."""
    user = User(
        email="user@test.com",
        password_hash=hash_password("password123"),
        subscription_tier="freemium",
        credits=10.0,
        email_verified=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user."""
    user = User(
        email="admin@test.com",
        password_hash=hash_password("password123"),
        subscription_tier="pro",
        credits=100.0,
        email_verified=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_token():
    """Returns a callable to create a valid access token for a regular user."""

    def _create_token(user_id, email, is_admin=False):
        return create_test_token(user_id, email, is_admin)

    return _create_token


@pytest.fixture(scope="function")
def admin_token():
    """Returns a callable to create a valid access token for an admin user."""

    def _create_token(user_id, email, is_admin=True):
        return create_test_token(user_id, email, is_admin)

    return _create_token


@pytest.fixture(scope="function")
def client_authenticated(client, regular_user, user_token):
    """TestClient authenticated as regular user."""
    token = user_token(regular_user.id, regular_user.email)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client


@pytest.fixture(scope="function")
def admin_client(client, admin_user, admin_token):
    """TestClient authenticated as admin."""
    token = admin_token(admin_user.id, admin_user.email)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client


@pytest.fixture(scope="function")
def auth_headers(regular_user, user_token):
    """Return authorization headers for a regular user."""
    token = user_token(regular_user.id, regular_user.email)
    return {"Authorization": f"Bearer {token}"}


def create_test_token(user_id: str, email: str, is_admin: bool = False, expires_minutes: int = 15) -> str:
    """Helper function to create test JWT tokens."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
