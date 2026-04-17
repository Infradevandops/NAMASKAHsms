"""Tests for /api/tiers/current — the endpoint the dashboard tier card reads from.

Verifies that every user type gets the correct tier back so the dashboard
card and header badge display the right plan after the i18nReady gate was removed.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestDashboardTierEndpoint:
    """GET /api/tiers/current returns the correct tier for every user type."""

    def test_freemium_user_returns_freemium(self, authenticated_regular_client):
        resp = authenticated_regular_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "freemium"

    def test_payg_user_returns_payg(self, authenticated_pro_client, db, pro_user):
        # Re-use pro_user fixture but downgrade to payg for this test
        pro_user.subscription_tier = "payg"
        db.commit()
        resp = authenticated_pro_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "payg"

    def test_pro_user_returns_pro(self, authenticated_pro_client):
        resp = authenticated_pro_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "pro"

    def test_admin_user_returns_custom(self, authenticated_admin_client):
        """Admin must always return custom regardless of DB expiry state."""
        resp = authenticated_admin_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "custom"

    def test_admin_with_unknown_tier_returns_custom(
        self, authenticated_admin_client, db, admin_user
    ):
        """Admin with an unrecognised tier value still gets custom via bypass."""
        admin_user.subscription_tier = "unknown_tier"
        db.commit()
        resp = authenticated_admin_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "custom"

    def test_admin_ignores_expired_tier(
        self, authenticated_admin_client, db, admin_user
    ):
        """Admin bypass must fire before expiry logic — expired date is irrelevant."""
        admin_user.subscription_tier = "custom"
        admin_user.tier_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.commit()
        resp = authenticated_admin_client.get("/api/tiers/current")
        assert resp.status_code == 200
        assert resp.json()["current_tier"] == "custom"

    def test_expired_pro_downgrades_to_freemium(self, engine, db):
        """Non-admin with expired tier_expires_at must downgrade to freemium."""
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import sessionmaker

        from app.core.database import get_db
        from app.core.dependencies import get_current_user_id
        from app.models.user import User
        from main import app

        uid = "expired-pro-user"
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            user = User(
                id=uid,
                email="expired@example.com",
                password_hash="x",
                credits=10.0,
                subscription_tier="pro",
                tier_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                is_admin=False,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()

        def override_db():
            Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            s = Session()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user_id] = lambda: uid
        client = TestClient(app)
        try:
            resp = client.get("/api/tiers/current")
            assert resp.status_code == 200
            assert resp.json()["current_tier"] == "freemium"
        finally:
            app.dependency_overrides.clear()

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/tiers/current")
        assert resp.status_code == 401

    def test_response_contains_required_fields(self, authenticated_regular_client):
        """Dashboard JS reads current_tier and tier_info from this response."""
        resp = authenticated_regular_client.get("/api/tiers/current")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_tier" in data
        assert data["current_tier"] in {"freemium", "payg", "pro", "custom"}
