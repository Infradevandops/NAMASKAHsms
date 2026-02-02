"""Pytest configuration and fixtures for all tests."""


# Set testing mode before importing app

import os
from datetime import datetime, timedelta, timezone
from typing import Generator
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import get_settings
from app.core.database import get_db
from app.models.base import Base
from main import app
from app.models.user import User
from app.models.user import User
from app.utils.security import hash_password
from app.models.user import User
from app.models.user import User
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.payment_service import PaymentService
from app.services.credit_service import CreditService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.activity_service import ActivityService
from unittest.mock import MagicMock
from app.core.security_config import create_access_token
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.utils.security import create_access_token

os.environ["TESTING"] = "1"


settings = get_settings()

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_session(db: Session) -> Session:
    """Alias for db fixture for compatibility."""
    return db


@pytest.fixture
def client(db: Session) -> TestClient:
    """Create FastAPI test client with test database."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id():
    """Return test user ID."""
    return "test-user-123"


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""

    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db: Session):
    """Create a regular freemium user."""

    user = User(
        email="regular@example.com",
        password_hash=hash_password("password123"),  # Hash the password properly
        is_active=True,
        subscription_tier="freemium",
        credits=10.0,
        bonus_sms_balance=5.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pro_user(db: Session):
    """Create a pro tier user."""

    user = User(
        email="pro@example.com",
        password_hash="hashed_password",
        is_active=True,
        subscription_tier="pro",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user."""

    user = User(
        email="admin@example.com",
        password_hash="hashed_password",
        is_active=True,
        is_admin=True,
        subscription_tier="enterprise",
        credits=1000.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def payg_user(db: Session):
    """Create a pay-as-you-go user."""

    user = User(
        email="payg@example.com",
        password_hash="hashed_password",
        is_active=True,
        subscription_tier="payg",
        credits=50.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_verification_data():
    """Return test verification data."""
    return {
        "service_name": "telegram",
        "country": "US",
        "capability": "sms",
        "area_code": None,
        "carrier": None,
    }


@pytest.fixture
def auth_service(db: Session):
    """Create an AuthService instance."""

    return AuthService(db)


@pytest.fixture
def payment_service(db: Session):
    """Create a PaymentService instance."""

    return PaymentService(db)


@pytest.fixture
def credit_service(db: Session):
    """Create a CreditService instance."""

    return CreditService(db)


@pytest.fixture
def email_service(db: Session):
    """Create an EmailService instance."""

    return EmailService(db)


@pytest.fixture
def notification_service(db: Session):
    """Create a NotificationService instance."""

    return NotificationService(db)


@pytest.fixture
def activity_service(db: Session):
    """Create an ActivityService instance."""

    return ActivityService(db)


@pytest.fixture
def redis_client():
    """Create a mock Redis client."""

    mock_redis = MagicMock()
    # Mock xadd to return a message ID
    mock_redis.xadd.return_value = b"1234567890-0"
    # Mock xread to return messages
    mock_redis.xread.return_value = [[b"webhook_queue", [
        (b"1234567890-0", {b"webhook_id": b"test", b"event": b"test.event", b"data": b'{"test": "data"}'}), ], ]]
    return mock_redis


@pytest.fixture
def auth_token(test_user):
    """Generate a valid JWT token for test user."""

    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def authenticated_client(client, db, test_user):
    """Create an authenticated test client."""

    def override_get_db():
        yield db

    def override_get_current_user_id():
        return str(test_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_regular_client(client, db, regular_user):
    """Create an authenticated test client for regular user."""

def override_get_db():
        yield db

def override_get_current_user_id():
        return str(regular_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_pro_client(client, db, pro_user):
    """Create an authenticated test client for pro user."""

def override_get_db():
        yield db

def override_get_current_user_id():
        return str(pro_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_admin_client(client, db, admin_user):
    """Create an authenticated test client for admin user."""

def override_get_db():
        yield db

def override_get_current_user_id():
        return str(admin_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create authorization headers for a given user ID."""

def _auth_headers(user_id: str):
        token = create_access_token(data={"sub": str(user_id)})
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


def create_test_token(user_id: str, email: str = "test@test.com") -> str:
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture
def user_token():
    """Fixture to create JWT tokens for testing."""
    return create_test_token
