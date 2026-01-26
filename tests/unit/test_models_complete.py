from datetime import datetime, timezone

import pytest

from app.models.api_key import APIKey
from app.models.notification import Notification
from app.models.transaction import Transaction
from app.models.user import User, Webhook


class TestModelsComplete:
    """Tests for database models."""

    def test_user_model(self, db_session):
        """Test User model CRUD and methods."""
        user = User(
            email="model_test@example.com",
            password_hash="hash",
            subscription_tier="freemium",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.is_active is True
        assert user.is_admin is False

        # Update
        user.is_admin = True
        db_session.commit()
        db_session.refresh(user)
        assert user.is_admin is True

    def test_webhook_model(self, db_session, regular_user):
        """Test Webhook model."""
        webhook = Webhook(
            user_id=regular_user.id,
            url="https://example.com/hook",
            events="test.event",
            is_active=True,
        )
        db_session.add(webhook)
        db_session.commit()

        assert webhook.id is not None
        assert webhook.user_id == regular_user.id

    def test_api_key_model(self, db_session, regular_user):
        """Test APIKey model."""
        api_key = APIKey(
            user_id=regular_user.id,
            name="Model Key",
            key_hash="hash",
            key_preview="preview",
            is_active=True,
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.id is not None
        assert api_key.last_used is None

    def test_transaction_model(self, db_session, regular_user):
        """Test Transaction model."""
        transaction = Transaction(user_id=regular_user.id, amount=10.5, type="credit", description="Test")
        db_session.add(transaction)
        db_session.commit()

        assert transaction.id is not None
        assert transaction.amount == 10.5

    def test_notification_model(self, db_session, regular_user):
        """Test Notification model."""
        notification = Notification(user_id=regular_user.id, type="info", title="Test", message="Test Message")
        db_session.add(notification)
        db_session.commit()

        assert notification.id is not None
        assert notification.is_read is False
