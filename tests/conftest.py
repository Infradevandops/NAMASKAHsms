"""Pytest configuration and fixtures for all tests."""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_db
from app.models.base import Base
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
    from app.models.user import User

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
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
