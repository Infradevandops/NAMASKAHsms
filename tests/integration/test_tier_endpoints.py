"""Integration tests for tier upgrade and cancel endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from main import app


def _make_client(engine, user_id: str):
    def override_db():
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        s = Session()
        try:
            yield s
        finally:
            s.close()

    def override_user():
        return user_id

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = override_user
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _create_user(db, user_id, tier, expires_at=None):
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        password_hash="x",
        credits=50.0,
        subscription_tier=tier,
        tier_expires_at=expires_at,
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    return user


class TestUpgradeTier:

    def test_upgrade_returns_paystack_url(self, engine, db):
        _create_user(db, "upgrade-user-1", "freemium")
        client = _make_client(engine, "upgrade-user-1")

        mock_payment = {
            "authorization_url": "https://paystack.com/pay/test123",
            "reference": "ref_test123",
            "payment_id": "ref_test123",
            "access_code": "acc_test",
        }
        with patch("app.api.billing.tier_endpoints.TierManager") as MockTM, \
             patch("app.api.billing.tier_endpoints.PaymentService") as MockPS:
            MockTM.return_value.get_user_tier.return_value = "freemium"
            MockPS.return_value.initialize_payment = AsyncMock(return_value=mock_payment)
            with patch("app.api.billing.tier_endpoints.TierConfig.get_tier_config") as mock_cfg:
                mock_cfg.return_value = {"monthly_fee_usd": 25.0}
                resp = client.post("/api/billing/tiers/upgrade?target_tier=pro")

        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert data["authorization_url"] == "https://paystack.com/pay/test123"

    def test_upgrade_metadata_contains_upgrade_to(self, engine, db):
        _create_user(db, "upgrade-user-2", "freemium")
        client = _make_client(engine, "upgrade-user-2")

        captured_metadata = {}

        async def capture_payment(**kwargs):
            captured_metadata.update(kwargs.get("metadata", {}))
            return {
                "authorization_url": "https://paystack.com/pay/x",
                "reference": "ref_x",
                "payment_id": "ref_x",
                "access_code": "acc_x",
            }

        with patch("app.api.billing.tier_endpoints.TierManager") as MockTM, \
             patch("app.api.billing.tier_endpoints.PaymentService") as MockPS, \
             patch("app.api.billing.tier_endpoints.TierConfig.get_tier_config") as mock_cfg:
            MockTM.return_value.get_user_tier.return_value = "freemium"
            MockPS.return_value.initialize_payment = capture_payment
            mock_cfg.return_value = {"monthly_fee_usd": 25.0}
            client.post("/api/billing/tiers/upgrade?target_tier=pro")

        assert captured_metadata.get("upgrade_to") == "pro"

    def test_upgrade_to_same_tier_rejected(self, engine, db):
        _create_user(db, "upgrade-user-3", "pro")
        client = _make_client(engine, "upgrade-user-3")
        with patch("app.api.billing.tier_endpoints.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "pro"
            resp = client.post("/api/billing/tiers/upgrade?target_tier=pro")
        assert resp.status_code == 400

    def test_upgrade_to_lower_tier_rejected(self, engine, db):
        _create_user(db, "upgrade-user-4", "custom")
        client = _make_client(engine, "upgrade-user-4")
        with patch("app.api.billing.tier_endpoints.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "custom"
            resp = client.post("/api/billing/tiers/upgrade?target_tier=pro")
        assert resp.status_code == 400


class TestCancelSubscription:

    def test_cancel_clears_renews_at(self, engine, db):
        from app.models.user_preference import UserPreference
        user = _create_user(
            db, "cancel-user-1", "pro",
            expires_at=datetime.now(timezone.utc) + timedelta(days=20)
        )
        pref = UserPreference(
            user_id=user.id,
            subscription_renews_at=datetime.now(timezone.utc) + timedelta(days=20),
        )
        db.add(pref)
        db.commit()

        client = _make_client(engine, "cancel-user-1")
        resp = client.post("/api/billing/tiers/cancel")
        assert resp.status_code == 200

        db.refresh(pref)
        assert pref.subscription_renews_at is None

    def test_cancel_preserves_tier_until_expiry(self, engine, db):
        expires = datetime.now(timezone.utc) + timedelta(days=20)
        user = _create_user(db, "cancel-user-2", "pro", expires_at=expires)
        client = _make_client(engine, "cancel-user-2")
        resp = client.post("/api/billing/tiers/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_tier"] == "pro"
        assert data["effective_date"] is not None

    def test_freemium_user_cannot_cancel(self, engine, db):
        _create_user(db, "cancel-user-3", "freemium")
        client = _make_client(engine, "cancel-user-3")
        resp = client.post("/api/billing/tiers/cancel")
        assert resp.status_code == 400
