"""Integration tests for API key endpoint tier gating."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from main import app


def _make_client(engine, user_id: str):
    """Create a test client with a fixed user_id override."""
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


class TestApiKeyTierGating:

    def test_payg_user_cannot_list_keys(self, engine, db):
        user = User(
            id="payg-gate-user",
            email="payg@example.com",
            password_hash="x",
            credits=10.0,
            subscription_tier="payg",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        client = _make_client(engine, "payg-gate-user")
        # require_payment_method also needs a balance — user has 10.0 so that passes,
        # but require_pro gate should reject payg
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "payg"
            resp = client.get("/api/keys/")
        assert resp.status_code == 402

    def test_pro_user_can_list_keys(self, engine, db):
        user = User(
            id="pro-gate-user",
            email="pro@example.com",
            password_hash="x",
            credits=10.0,
            subscription_tier="pro",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        client = _make_client(engine, "pro-gate-user")
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "pro"
            resp = client.get("/api/keys/")
        assert resp.status_code == 200

    def test_freemium_user_cannot_generate_key(self, engine, db):
        user = User(
            id="free-gate-user",
            email="free@example.com",
            password_hash="x",
            credits=0.0,
            subscription_tier="freemium",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        client = _make_client(engine, "free-gate-user")
        with patch("app.core.dependencies.TierManager") as MockTM:
            MockTM.return_value.get_user_tier.return_value = "freemium"
            resp = client.post("/api/keys/generate", json={"name": "test"})
        assert resp.status_code == 402

    def test_custom_user_can_generate_key(self, engine, db):
        user = User(
            id="custom-gate-user",
            email="custom@example.com",
            password_hash="x",
            credits=10.0,
            subscription_tier="custom",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        client = _make_client(engine, "custom-gate-user")
        with patch("app.core.dependencies.TierManager") as MockTM, \
             patch("app.services.tier_manager.TierConfig.get_tier_config") as mock_cfg:
            MockTM.return_value.get_user_tier.return_value = "custom"
            MockTM.return_value.can_create_api_key.return_value = (True, "")
            mock_cfg.return_value = {"api_key_limit": -1}
            resp = client.post("/api/keys/generate", json={"name": "my key"})
        assert resp.status_code == 201
