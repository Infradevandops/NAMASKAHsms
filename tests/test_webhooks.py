"""Tests for webhook management functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, Webhook
from main import app

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user with PAYG tier."""
    user = User(
        email="webhook_test@example.com",
        password_hash="hashed_password",
        tier="payg",
        credits=100.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    # Mock JWT token generation
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


class TestWebhookManagement:
    """Test suite for webhook management."""

    def test_list_webhooks_empty(self, test_user, auth_headers, db):
        """Test listing webhooks when none exist."""
        response = client.get("/webhooks", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    def test_create_webhook_success(self, test_user, auth_headers, db):
        """Test creating a new webhook."""
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["verification.completed", "message.received"],
        }

        response = client.post("/webhooks", json=webhook_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert "secret" in data["data"]
        assert len(data["data"]["secret"]) == 32  # 16 bytes hex = 32 chars

    def test_create_webhook_invalid_url(self, test_user, auth_headers):
        """Test creating webhook with invalid URL."""
        webhook_data = {
            "name": "Invalid Webhook",
            "url": "not-a-valid-url",
            "events": ["*"],
        }

        response = client.post("/webhooks", json=webhook_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_create_webhook_requires_payg(self, db):
        """Test that webhook creation requires PAYG tier."""
        # Create freemium user
        freemium_user = User(
            email="freemium@example.com",
            password_hash="hashed",
            tier="freemium",
            credits=10.0,
        )
        db.add(freemium_user)
        db.commit()

        headers = {"Authorization": f"Bearer test_token_{freemium_user.id}"}
        webhook_data = {
            "name": "Test",
            "url": "https://example.com/webhook",
            "events": ["*"],
        }

        response = client.post("/webhooks", json=webhook_data, headers=headers)

        assert response.status_code == 403  # Forbidden

    def test_list_webhooks_with_data(self, test_user, auth_headers, db):
        """Test listing webhooks when some exist."""
        # Create test webhooks
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

        response = client.get("/webhooks", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["name"] == "Webhook 1"
        assert data["data"][0]["is_active"] is True
        assert data["data"][1]["is_active"] is False

    def test_delete_webhook_success(self, test_user, auth_headers, db):
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

        response = client.delete(f"/webhooks/{webhook.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify deletion
        deleted = db.query(Webhook).filter(Webhook.id == webhook.id).first()
        assert deleted is None

    def test_delete_webhook_not_found(self, test_user, auth_headers):
        """Test deleting non-existent webhook."""
        response = client.delete("/webhooks/nonexistent_id", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_webhook_wrong_user(self, test_user, auth_headers, db):
        """Test that users can't delete other users' webhooks."""
        # Create another user
        other_user = User(
            email="other@example.com",
            password_hash="hashed",
            tier="payg",
            credits=100.0,
        )
        db.add(other_user)
        db.commit()

        # Create webhook for other user
        webhook = Webhook(
            user_id=other_user.id,
            name="Other's Webhook",
            url="https://example.com/webhook",
            events="*",
            secret="secret",
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)

        # Try to delete with test_user's credentials
        response = client.delete(f"/webhooks/{webhook.id}", headers=auth_headers)

        assert response.status_code == 404  # Not found (filtered by user_id)

    def test_test_webhook_success(self, test_user, auth_headers, db):
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

        response = client.post(f"/webhooks/{webhook.id}/test", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Test ping sent" in data["message"]

    def test_test_webhook_not_found(self, test_user, auth_headers):
        """Test testing non-existent webhook."""
        response = client.post("/webhooks/nonexistent_id/test", headers=auth_headers)

        assert response.status_code == 404

    def test_webhook_events_validation(self, test_user, auth_headers):
        """Test that webhook events are properly validated."""
        webhook_data = {
            "name": "Event Test",
            "url": "https://example.com/webhook",
            "events": [
                "verification.completed",
                "verification.failed",
                "message.received",
                "payment.completed",
            ],
        }

        response = client.post("/webhooks", json=webhook_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_webhook_secret_uniqueness(self, test_user, auth_headers, db):
        """Test that each webhook gets a unique secret."""
        webhook_data = {
            "name": "Webhook",
            "url": "https://example.com/webhook",
            "events": ["*"],
        }

        response1 = client.post("/webhooks", json=webhook_data, headers=auth_headers)
        response2 = client.post("/webhooks", json=webhook_data, headers=auth_headers)

        secret1 = response1.json()["data"]["secret"]
        secret2 = response2.json()["data"]["secret"]

        assert secret1 != secret2

    def test_webhook_url_https_required(self, test_user, auth_headers):
        """Test that webhook URLs must use HTTPS."""
        webhook_data = {
            "name": "HTTP Webhook",
            "url": "http://example.com/webhook",  # HTTP not HTTPS
            "events": ["*"],
        }

        response = client.post("/webhooks", json=webhook_data, headers=auth_headers)

        # Should fail validation (pydantic HttpUrl requires https in production)
        assert response.status_code in [422, 400]


class TestWebhookIntegration:
    """Integration tests for webhook functionality."""

    def test_webhook_lifecycle(self, test_user, auth_headers, db):
        """Test complete webhook lifecycle: create, list, test, delete."""
        # Create
        create_response = client.post(
            "/webhooks",
            json={
                "name": "Lifecycle Test",
                "url": "https://example.com/webhook",
                "events": ["verification.completed"],
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        webhook_id = create_response.json()["data"]["id"]

        # List
        list_response = client.get("/webhooks", headers=auth_headers)
        assert len(list_response.json()["data"]) == 1

        # Test
        test_response = client.post(
            f"/webhooks/{webhook_id}/test", headers=auth_headers
        )
        assert test_response.status_code == 200

        # Delete
        delete_response = client.delete(f"/webhooks/{webhook_id}", headers=auth_headers)
        assert delete_response.status_code == 200

        # Verify deletion
        final_list = client.get("/webhooks", headers=auth_headers)
        assert len(final_list.json()["data"]) == 0

    def test_multiple_webhooks_per_user(self, test_user, auth_headers):
        """Test that users can create multiple webhooks."""
        webhooks = [
            {
                "name": f"Webhook {i}",
                "url": f"https://example.com/webhook{i}",
                "events": ["*"],
            }
            for i in range(5)
        ]

        for webhook_data in webhooks:
            response = client.post("/webhooks", json=webhook_data, headers=auth_headers)
            assert response.status_code == 200

        list_response = client.get("/webhooks", headers=auth_headers)
        assert len(list_response.json()["data"]) == 5


# Run tests with: pytest tests/test_webhooks.py -v
