"""Pytest configuration and fixtures for all tests."""

from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base

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
