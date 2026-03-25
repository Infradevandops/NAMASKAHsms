"""Test configuration and fixtures."""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction, PaymentLog
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.notification_analytics import NotificationAnalytics
from app.models.api_key import APIKey
from app.models.subscription_tier import SubscriptionTier
from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.affiliate import AffiliateProgram, AffiliateApplication, AffiliateCommission
from app.models.commission import CommissionTier, RevenueShare
from app.models.blacklist import NumberBlacklist
from app.models.kyc import KYCProfile
from app.models.refund import Refund
from app.models.whitelabel import WhiteLabelConfig
from app.models.whitelabel_enhanced import WhiteLabelAsset, WhiteLabelDomain, WhiteLabelTheme
from app.models.pricing_template import PricingTemplate
from app.models.device_token import DeviceToken
from app.models.user_preference import UserPreference
from app.models.user_quota import UserQuota, MonthlyQuotaUsage
from app.models.balance_transaction import BalanceTransaction
from app.models.carrier_analytics import CarrierAnalytics
from app.models.verification_preset import VerificationPreset
from app.models.waitlist import Waitlist
from app.models.reseller import ResellerAccount, SubAccount, SubAccountTransaction, CreditAllocation, BulkOperation
from app.utils.security import create_access_token
from main import app


def create_test_token(user_id: str, email: str = "test@example.com", **kwargs) -> str:
    return create_access_token({"sub": user_id, "email": email})


@pytest.fixture(scope="session", autouse=True)
def check_services():
    pass


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session(db):
    return db


@pytest.fixture
def client(engine):
    def override_get_db():
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id():
    return "test-user-123"


@pytest.fixture
def test_user(db, test_user_id):
    user = db.query(User).filter(User.id == test_user_id).first()
    if not user:
        user = User(
            id=test_user_id,
            email="test@example.com",
            password_hash="$2b$12$test_hash",
            credits=100.0,
            subscription_tier="pro",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    user = db.query(User).filter(User.id == "admin-user-123").first()
    if not user:
        user = User(
            id="admin-user-123",
            email="admin@example.com",
            password_hash="$2b$12$admin_hash",
            credits=1000.0,
            subscription_tier="custom",
            is_admin=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def regular_user(db):
    user = db.query(User).filter(User.id == "regular-user-123").first()
    if not user:
        user = User(
            id="regular-user-123",
            email="regular@example.com",
            password_hash="$2b$12$regular_hash",
            credits=50.0,
            subscription_tier="freemium",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def payg_user(db):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"payg-{uid[:8]}@example.com",
        password_hash="$2b$12$test_hash",
        credits=50.0,
        subscription_tier="payg",
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pro_user(db):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"pro-{uid[:8]}@example.com",
        password_hash="$2b$12$test_hash",
        credits=100.0,
        subscription_tier="pro",
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    def _make(user_id: str = None, email: str = None):
        uid = user_id or test_user.id
        em = email or test_user.email
        return create_test_token(uid, em)
    return _make


@pytest.fixture
def admin_token(admin_user):
    return create_test_token(admin_user.id, admin_user.email)


@pytest.fixture
def regular_user_token(regular_user):
    return create_test_token(regular_user.id, regular_user.email)


@pytest.fixture
def pro_user_token(pro_user):
    return create_test_token(pro_user.id, pro_user.email)


@pytest.fixture
def freemium_user_token(db):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"freemium-{uid[:8]}@example.com",
        password_hash="$2b$12$test_hash",
        credits=0.0,
        subscription_tier="freemium",
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    return create_test_token(uid, user.email)


@pytest.fixture
def redis_client():
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def auth_headers_factory():
    def _make(user_id: str) -> dict:
        token = create_test_token(user_id)
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest.fixture
def test_verification(db, test_user):
    verification = Verification(
        id="test-verification-123",
        user_id=test_user.id,
        phone_number="+1234567890",
        service="test_service",
        status="pending",
        cost=2.50,
        created_at=datetime.now(timezone.utc),
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


@pytest.fixture
def test_transaction(db, test_user):
    transaction = Transaction(
        id="test-transaction-123",
        user_id=test_user.id,
        type="credit",
        amount=20.0,
        description="Test credit",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def _make_client_with_user(engine, user_id):
    def override_get_db():
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = lambda: str(user_id)
    return TestClient(app)


@pytest.fixture
def authenticated_client(test_user, engine):
    client = _make_client_with_user(engine, test_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_regular_client(regular_user, engine):
    client = _make_client_with_user(engine, regular_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_admin_client(admin_user, engine):
    client = _make_client_with_user(engine, admin_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_pro_client(pro_user, engine):
    client = _make_client_with_user(engine, pro_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(admin_user, engine):
    client = _make_client_with_user(engine, admin_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def regular_client(regular_user, engine):
    client = _make_client_with_user(engine, regular_user.id)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_paystack_response():
    return {
        "status": True,
        "message": "Authorization URL created",
        "data": {
            "authorization_url": "https://checkout.paystack.com/test123",
            "access_code": "test_access_code",
            "reference": "test_reference_123",
        },
    }


@pytest.fixture
def mock_verification_response():
    return {
        "status": "success",
        "verification_id": "test_verification_123",
        "phone_number": "+1234567890",
        "service": "test_service",
        "cost": 2.50,
    }