"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base
from main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    from app.models.user import User
    from app.utils.security import hash_password
    from .fixtures import TEST_CREDENTIALS

    user = User(
        id="test_user_123",
        email="test@example.com",
        password_hash=hash_password(TEST_CREDENTIALS["user_password"]),
        credits=10.0,
        free_verifications=1.0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client):
    """Authentication headers for test user."""
    from .fixtures import TEST_CREDENTIALS

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": TEST_CREDENTIALS["user_password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    """Create admin user."""
    from app.models.user import User
    from app.utils.security import hash_password
    from .fixtures import TEST_CREDENTIALS

    user = User(
        id="admin_user_123",
        email="admin@example.com",
        password_hash=hash_password(TEST_CREDENTIALS["admin_password"]),
        credits=100.0,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
