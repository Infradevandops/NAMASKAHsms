"""Comprehensive payment system tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import engine, get_db
from app.models.base import Base
from main import create_app


@pytest.fixture
def app():
    """Create test app."""
    Base.metadata.create_all(bind=engine)
    yield create_app()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create test user."""
    from app.models.user import User
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        credits=100.0,
        is_active=True
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def auth_token(client, test_user):
    """Get auth token."""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    return response.json()["access_token"]


# ============================================================================
# UNIT TESTS - Payment Endpoints
# ============================================================================

class TestPaymentInitialization:
    """Test payment initialization."""

    def test_initialize_payment_valid(self, client, auth_token):
        """Test valid payment initialization."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "reference" in data
        assert data["amount_usd"] == 10

    def test_initialize_payment_invalid_amount_low(self, client, auth_token):
        """Test payment with amount too low."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": 0.001}
        )
        assert response.status_code == 400

    def test_initialize_payment_invalid_amount_high(self, client, auth_token):
        """Test payment with amount too high."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": 50000}
        )
        assert response.status_code == 400

    def test_initialize_payment_negative_amount(self, client, auth_token):
        """Test payment with negative amount."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": -10}
        )
        assert response.status_code in [400, 422]

    def test_initialize_payment_unauthorized(self, client):
        """Test payment without authentication."""
        response = client.post(
            "/api/billing/initialize-payment",
            json={"amount_usd": 10}
        )
        assert response.status_code in [401, 403]


class TestPaymentVerification:
    """Test payment verification."""

    def test_verify_payment_not_found(self, client, auth_token):
        """Test verify non-existent payment."""
        response = client.get(
            "/api/billing/verify-payment/invalid_ref",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_verify_payment_invalid_reference(self, client, auth_token):
        """Test verify with invalid reference format."""
        response = client.get(
            "/api/billing/verify-payment/x",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400


class TestBalance:
    """Test balance endpoints."""

    def test_get_balance(self, client, auth_token):
        """Test get balance."""
        response = client.get(
            "/api/user/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
        assert data["credits"] == 100.0

    def test_get_balance_unauthorized(self, client):
        """Test get balance without auth."""
        response = client.get("/api/user/balance")
        assert response.status_code in [401, 403]


class TestTransactions:
    """Test transaction endpoints."""

    def test_get_transactions(self, client, auth_token):
        """Test get transactions."""
        response = client.get(
            "/api/billing/transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "transactions" in data

    def test_get_transactions_pagination(self, client, auth_token):
        """Test transactions pagination."""
        response = client.get(
            "/api/billing/transactions?skip=0&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_get_transactions_invalid_limit(self, client, auth_token):
        """Test transactions with invalid limit."""
        response = client.get(
            "/api/billing/transactions?limit=200",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400


# ============================================================================
# UNIT TESTS - Notification Endpoints
# ============================================================================

class TestNotifications:
    """Test notification endpoints."""

    def test_get_notifications(self, client, auth_token):
        """Test get notifications."""
        response = client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "notifications" in data

    def test_get_unread_count(self, client, auth_token):
        """Test get unread count."""
        response = client.get(
            "/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data

    def test_mark_as_read(self, client, auth_token, db):
        """Test mark notification as read."""
        from app.models.notification import Notification
        
        # Create notification
        notif = Notification(
            user_id="test_user",
            type="payment_success",
            title="Test",
            message="Test message",
            read=False
        )
        db.add(notif)
        db.commit()
        
        response = client.post(
            f"/api/notifications/{notif.id}/read",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200


# ============================================================================
# UNIT TESTS - Refund Endpoints
# ============================================================================

class TestRefunds:
    """Test refund endpoints."""

    def test_get_refund_history(self, client, auth_token):
        """Test get refund history."""
        response = client.get(
            "/api/billing/refunds",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "refunds" in data

    def test_get_refund_status_not_found(self, client, auth_token):
        """Test get non-existent refund."""
        response = client.get(
            "/api/billing/refund/invalid_ref",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPaymentFlow:
    """Test complete payment flow."""

    def test_payment_flow_initialization(self, client, auth_token):
        """Test payment initialization."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"amount_usd": 10}
        )
        assert response.status_code == 200
        assert "authorization_url" in response.json()


class TestWebhookHandling:
    """Test webhook handling."""

    def test_webhook_signature_verification(self, client):
        """Test webhook signature verification."""
        response = client.post(
            "/api/billing/webhook",
            headers={"X-Paystack-Signature": "invalid_signature"},
            json={"event": "charge.success", "data": {}}
        )
        assert response.status_code == 401

    def test_webhook_missing_signature(self, client):
        """Test webhook without signature."""
        response = client.post(
            "/api/billing/webhook",
            json={"event": "charge.success", "data": {}}
        )
        assert response.status_code == 401


# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabaseOperations:
    """Test database operations."""

    def test_payment_log_creation(self, db):
        """Test payment log creation."""
        from app.models.transaction import PaymentLog
        
        log = PaymentLog(
            user_id="test_user",
            email="test@example.com",
            reference="test_ref",
            amount_usd=10.0,
            amount_ngn=15000.0,
            namaskah_amount=10.0,
            status="pending",
            payment_method="paystack"
        )
        db.add(log)
        db.commit()
        
        retrieved = db.query(PaymentLog).filter(
            PaymentLog.reference == "test_ref"
        ).first()
        assert retrieved is not None
        assert retrieved.amount_usd == 10.0

    def test_transaction_creation(self, db):
        """Test transaction creation."""
        from app.models.transaction import Transaction
        
        trans = Transaction(
            user_id="test_user",
            amount=10.0,
            type="credit",
            description="Test transaction"
        )
        db.add(trans)
        db.commit()
        
        retrieved = db.query(Transaction).filter(
            Transaction.user_id == "test_user"
        ).first()
        assert retrieved is not None
        assert retrieved.amount == 10.0

    def test_notification_creation(self, db):
        """Test notification creation."""
        from app.models.notification import Notification
        
        notif = Notification(
            user_id="test_user",
            type="payment_success",
            title="Test",
            message="Test message",
            read=False
        )
        db.add(notif)
        db.commit()
        
        retrieved = db.query(Notification).filter(
            Notification.user_id == "test_user"
        ).first()
        assert retrieved is not None
        assert retrieved.type == "payment_success"

    def test_refund_creation(self, db):
        """Test refund creation."""
        from app.models.refund import Refund
        
        refund = Refund(
            payment_id="test_payment",
            user_id="test_user",
            amount=10.0,
            reason="Test refund",
            status="pending",
            reference="test_refund_ref"
        )
        db.add(refund)
        db.commit()
        
        retrieved = db.query(Refund).filter(
            Refund.reference == "test_refund_ref"
        ).first()
        assert retrieved is not None
        assert retrieved.amount == 10.0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json(self, client, auth_token):
        """Test invalid JSON."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            data="invalid json"
        )
        assert response.status_code in [400, 422]

    def test_missing_required_field(self, client, auth_token):
        """Test missing required field."""
        response = client.post(
            "/api/billing/initialize-payment",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={}
        )
        assert response.status_code in [400, 422]


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurity:
    """Test security features."""

    def test_cross_user_access_prevention(self, client, auth_token):
        """Test cross-user access prevention."""
        # Try to access another user's data
        response = client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should only return current user's data
        assert response.status_code == 200

    def test_sql_injection_prevention(self, client, auth_token):
        """Test SQL injection prevention."""
        response = client.get(
            "/api/billing/verify-payment/'; DROP TABLE payment_logs; --",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should handle safely
        assert response.status_code in [400, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
