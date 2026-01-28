"""Pytest configuration and fixtures for all tests."""

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.models.base import Base as ModelBase
from main import app


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
    ModelBase.metadata.create_all(bind=engine)
    yield engine
    ModelBase.metadata.drop_all(bind=engine)


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
def client(db: Session):
    """Create test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client, db: Session):
    """Create test user and return auth token."""
    from app.models.user import User
    from app.core.config import get_settings
    import jwt
    from datetime import datetime, timedelta

    # Create test user
    test_user = User(
        id="test-user-123",
        email="test@example.com",
        phone_number="+1234567890",
        password_hash="hashed_password",
        email_verified=True,
        credits=100.0,
    )
    db.add(test_user)
    db.commit()

    # Generate JWT token
    settings = get_settings()
    payload = {
        "user_id": test_user.id,
        "email": test_user.email,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    return token


@pytest.fixture
def auth_headers(auth_token: str):
    """Return authorization headers with token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_user_id():
    """Return test user ID."""
    return "test-user-123"


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
