"""Tests for webhook management functionality."""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User, Webhook


@pytest.fixture
def test_user(db: Session):
    """Create a test user with PAYG tier."""
    user = User(
        email="webhook_test@example.com",
        password_hash="$2b$12$K7Kn0bFc6ne3EY2F008AvOVlOgDcWFPJV2LbZnxlZh/Bzu.Au3fPO",
        subscription_tier="payg",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def webhook_client(test_user, engine):
    """Create authenticated client for webhook tests."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from app.core.database import get_db
    from app.core.dependencies import get_current_user_id
    from main import app

    def override_get_db():
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = lambda: str(test_user.id)

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestWebhookManagement:
    """Test suite for webhook management."""

    def test_list_webhooks_empty(self, webhook_client, test_user, db):
        """Test listing webhooks when none exist."""
        response = webhook_client.get("/api/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["webhooks"]) == 0

    def test_create_webhook_success(self, webhook_client, test_user, db):
        """Test creating a new webhook."""
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["verification.completed", "message.received"],
        }

        response = webhook_client.post("/api/webhooks", json=webhook_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "secret" in data["data"]
        assert len(data["data"]["secret"]) == 32

    def test_create_webhook_invalid_url(self, webhook_client, test_user):
        """Test creating webhook with invalid URL."""
        webhook_data = {
            "name": "Invalid Webhook",
            "url": "not-a-valid-url",
            "events": ["*"],
        }

        response = webhook_client.post("/api/webhooks", json=webhook_data)
        assert response.status_code == 422

    def test_list_webhooks_with_data(self, webhook_client, test_user, db):
        """Test listing webhooks when some exist."""
        webhook1 = Webhook(
            user_id=test_user.id,
            name="Webhook 1",
            url="https://example.com/webhook1",
            events="verification.completed",
            secret="secret1",
            is_active=True,
        )
        webhook2 = Webhook(
            user_id=test_user.id,
            name="Webhook 2",
            url="https://example.com/webhook2",
            events="*",
            secret="secret2",
            is_active=False,
        )
        db.add_all([webhook1, webhook2])
        db.commit()

        response = webhook_client.get("/api/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["webhooks"]) == 2

    def test_delete_webhook_success(self, webhook_client, test_user, db):
        """Test deleting a webhook."""
        webhook = Webhook(
            user_id=test_user.id,
            name="To Delete",
            url="https://example.com/webhook",
            events="*",
            secret="secret",
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        response = webhook_client.delete(f"/api/webhooks/{webhook.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

        deleted = db.query(Webhook).filter(Webhook.id == webhook.id).first()
        assert deleted is None

    def test_delete_webhook_not_found(self, webhook_client, test_user):
        """Test deleting non-existent webhook."""
        response = webhook_client.delete("/api/webhooks/nonexistent_id")
        assert response.status_code == 404

    def test_test_webhook_success(self, webhook_client, test_user, db):
        """Test sending a test ping to webhook."""
        webhook = Webhook(
            user_id=test_user.id,
            name="Test Webhook",
            url="https://example.com/webhook",
            events="*",
            secret="secret",
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        response = webhook_client.post(f"/api/webhooks/{webhook.id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_webhook_secret_uniqueness(self, webhook_client, test_user, db):
        """Test that each webhook gets a unique secret."""
        webhook_data = {
            "name": "Webhook",
            "url": "https://example.com/webhook",
            "events": ["*"],
        }

        response1 = webhook_client.post("/api/webhooks", json=webhook_data)
        response2 = webhook_client.post("/api/webhooks", json=webhook_data)

        secret1 = response1.json()["data"]["secret"]
        secret2 = response2.json()["data"]["secret"]

        assert secret1 != secret2
