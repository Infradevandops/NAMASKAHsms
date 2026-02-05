"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction
from main import app


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db(engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
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
def test_user(db, test_user_id):
    """Create test user."""
    user = User(
        id=test_user_id,
        email="test@example.com",
        password_hash="$2b$12$test_hash",
        credits=100.0,
        tier="pro",
        is_admin=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    user = User(
        id="admin-user-123",
        email="admin@example.com",
        password_hash="$2b$12$admin_hash",
        credits=1000.0,
        tier="custom",
        is_admin=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db):
    """Create regular user."""
    user = User(
        id="regular-user-123",
        email="regular@example.com",
        password_hash="$2b$12$regular_hash",
        credits=50.0,
        tier="freemium",
        is_admin=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers():
    """Return authentication headers."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def test_verification(db, test_user):
    """Create test verification."""
    verification = Verification(
        id="test-verification-123",
        user_id=test_user.id,
        phone_number="+1234567890",
        service="test_service",
        status="pending",
        cost=2.50,
        created_at=datetime.now(timezone.utc)
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


@pytest.fixture
def test_transaction(db, test_user):
    """Create test transaction."""
    transaction = Transaction(
        id="test-transaction-123",
        user_id=test_user.id,
        type="credit",
        amount=20.0,
        description="Test credit",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@pytest.fixture
def authenticated_client(client, test_user, db):
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
def admin_client(client, admin_user, db):
    """Create an admin test client."""
def override_get_db():
        yield db

def override_get_current_user_id():
        return str(admin_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def regular_client(client, regular_user, db):
    """Create a regular user test client."""
def override_get_db():
        yield db

def override_get_current_user_id():
        return str(regular_user.id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_paystack_response():
    """Mock Paystack API response."""
    return {
        "status": True,
        "message": "Authorization URL created",
        "data": {
            "authorization_url": "https://checkout.paystack.com/test123",
            "access_code": "test_access_code",
            "reference": "test_reference_123"
        }
    }


@pytest.fixture
def mock_verification_response():
    """Mock verification service response."""
    return {
        "status": "success",
        "verification_id": "test_verification_123",
        "phone_number": "+1234567890",
        "service": "test_service",
        "cost": 2.50
    }
