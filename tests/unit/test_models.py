

from datetime import datetime, timezone
from app.models.user import (

    NotificationSettings,
    Referral,
    Subscription,
    User,
    Webhook,
)


class TestModels:

    def test_user_defaults(self, db_session):

        user = User(email="test_model@example.com")
        db_session.add(user)
        db_session.commit()

        assert user.credits == 0.0
        assert user.is_active is True
        assert user.subscription_tier == "freemium"
        assert user.is_admin is False
        assert user.is_moderator is False

    def test_webhook_model(self, db_session):

        webhook = Webhook(
            user_id="user_123",
            url="https://hooks.com/123",
            name="My Hook",
            secret="shhh",
        )
        db_session.add(webhook)
        db_session.commit()

        assert webhook.is_active is True
        assert webhook.events == "*"
        assert webhook.user_id == "user_123"

    def test_referral_model(self, db_session):

        ref = Referral(referrer_id="r1", referred_id="r2", reward_amount=5.0)
        db_session.add(ref)
        db_session.commit()
        assert ref.reward_amount == 5.0

    def test_subscription_model(self, db_session):

        sub = Subscription(user_id="u1", plan="pro", price=25.0, expires_at=datetime.now(timezone.utc))
        db_session.add(sub)
        db_session.commit()
        assert sub.status == "active"
        assert sub.plan == "pro"

    def test_notification_settings_model(self, db_session):

        settings = NotificationSettings(user_id="u1", email_on_sms=False)
        db_session.add(settings)
        db_session.commit()
        assert settings.email_on_sms is False
        assert settings.email_on_low_balance is True
        assert settings.low_balance_threshold == 1.0