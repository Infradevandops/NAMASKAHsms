"""Tests for tier endpoints.

from datetime import datetime, timezone
from app.models.user import User
from app.models.verification import Verification
from app.utils.security import hash_password

Feature: tier-system-rbac
Tests validate tier listing, current tier retrieval, and tier upgrade/downgrade functionality.
"""


class TestTierListEndpoint:

    """Tests for GET /api/tiers/ endpoint."""

    def test_list_tiers_returns_all_four_tiers(self, client):

        """Test that /api/tiers/ returns all 4 available tiers."""
        response = client.get("/api/tiers/")
        assert response.status_code == 200

        data = response.json()
        assert "tiers" in data
        tiers = data["tiers"]

        # Should have exactly 4 tiers
        assert len(tiers) == 4

        # Check tier names
        tier_names = {tier["tier"] for tier in tiers}
        assert tier_names == {"freemium", "payg", "pro", "custom"}

    def test_list_tiers_includes_required_fields(self, client):

        """Test that each tier includes all required fields."""
        response = client.get("/api/tiers/")
        assert response.status_code == 200

        data = response.json()
        tiers = data["tiers"]

        required_fields = {
            "tier",
            "name",
            "price_monthly",
            "price_display",
            "quota_usd",
            "overage_rate",
            "features",
        }

        for tier in tiers:
            assert all(field in tier for field in required_fields)
            assert "api_access" in tier["features"]
            assert "support_level" in tier["features"]

    def test_list_tiers_pricing_is_correct(self, client):

        """Test that tier pricing is formatted correctly."""
        response = client.get("/api/tiers/")
        assert response.status_code == 200

        data = response.json()
        tiers = data["tiers"]

        # Freemium should be free
        freemium = next(t for t in tiers if t["tier"] == "freemium")
        assert freemium["price_monthly"] == 0
        assert "Free" in freemium["price_display"]

        # Pro tier should have price
        pro = next((t for t in tiers if t["tier"] == "pro"), None)
        if pro:
            assert pro["price_monthly"] > 0
            assert "$" in pro["price_display"]


class TestCurrentTierEndpoint:

        """Tests for GET /api/tiers/current endpoint."""

    def test_current_tier_returns_user_tier(self, client, regular_user, user_token):

        """Test that /api/tiers/current returns the user's current tier."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/api/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["current_tier"] == "freemium"
        assert data["tier_name"] == "Freemium"

    def test_current_tier_returns_all_required_fields(self, client, regular_user, user_token):

        """Test that /api/tiers/current returns all required fields."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/api/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        required_fields = {
            "current_tier",
            "tier_name",
            "price_monthly",
            "quota_usd",
            "quota_used_usd",
            "quota_remaining_usd",
            "sms_count",
            "within_quota",
            "overage_rate",
            "features",
        }

        assert all(field in data for field in required_fields)

    def test_current_tier_quota_calculations(self, client, regular_user, user_token, db):

        """Test that quota calculations are correct."""
        token = user_token(regular_user.id, regular_user.email)

        # Set some quota usage
        regular_user.monthly_quota_used = 5.0
        db.commit()

        response = client.get("/api/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["quota_used_usd"] == 5.0
        assert data["quota_remaining_usd"] >= 0

    def test_current_tier_sms_count(self, client, regular_user, user_token, db):

        """Test that SMS count is calculated correctly."""
        token = user_token(regular_user.id, regular_user.email)

        # Create some SMS verifications for this month
        for i in range(3):
            verification = Verification(
                id=f"sms_verify_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="completed",
                cost=0.05,
                created_at=datetime.now(timezone.utc),
            )
            db.add(verification)
        db.commit()

        response = client.get("/api/tiers/current", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["sms_count"] == 3

    def test_current_tier_requires_authentication(self, client):

        """Test that /api/tiers/current requires authentication."""
        response = client.get("/api/tiers/current")
        assert response.status_code == 401

    def test_current_tier_with_different_tiers(self, client, db, user_token):

        """Test current tier endpoint with different user tiers."""
        tiers_to_test = ["freemium", "payg", "pro", "custom"]

        for tier in tiers_to_test:
            user = User(
                id=f"user_{tier}",
                email=f"{tier}@test.com",
                password_hash=hash_password("password123"),
                email_verified=True,
                is_admin=False,
                credits=10.0,
                subscription_tier=tier,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
        db.commit()

        for tier in tiers_to_test:
            token = user_token(f"user_{tier}", f"{tier}@test.com")
            response = client.get("/api/tiers/current", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            data = response.json()
            assert data["current_tier"] == tier


class TestUpgradeTierEndpoint:

        """Tests for POST /api/tiers/upgrade endpoint."""

    def test_upgrade_tier_validates_hierarchy(self, client, regular_user, user_token, db):

        """Test that upgrade validates tier hierarchy."""
        token = user_token(regular_user.id, regular_user.email)

        # Freemium user should be able to upgrade to payg
        response = client.post(
            "/api/tiers/upgrade",
            json={"target_tier": "payg"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_tier"] == "payg"

        # Verify user tier was updated
        db.refresh(regular_user)
        assert regular_user.subscription_tier == "payg"

    def test_upgrade_tier_rejects_downgrade(self, client, db, user_token):

        """Test that upgrade rejects downgrade attempts."""
        user = User(
            id="payg_user",
            email="payg@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="payg",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = user_token("payg_user", "payg@test.com")

        # Try to downgrade from payg to freemium (should fail)
        response = client.post(
            "/api/tiers/upgrade",
            json={"target_tier": "freemium"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_upgrade_tier_rejects_same_tier(self, client, regular_user, user_token):

        """Test that upgrade rejects upgrading to same tier."""
        token = user_token(regular_user.id, regular_user.email)

        # Try to upgrade to same tier
        response = client.post(
            "/api/tiers/upgrade",
            json={"target_tier": "freemium"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_upgrade_tier_requires_target_tier(self, client, regular_user, user_token):

        """Test that upgrade requires target_tier parameter."""
        token = user_token(regular_user.id, regular_user.email)

        response = client.post("/api/tiers/upgrade", json={}, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400

    def test_upgrade_tier_requires_authentication(self, client):

        """Test that upgrade requires authentication."""
        response = client.post("/api/tiers/upgrade", json={"target_tier": "payg"})
        assert response.status_code == 401


class TestDowngradeTierEndpoint:

        """Tests for POST /api/tiers/downgrade endpoint."""

    def test_downgrade_tier_to_freemium(self, client, db, user_token):

        """Test that downgrade sets tier to freemium."""
        user = User(
            id="pro_user",
            email="pro@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = user_token("pro_user", "pro@test.com")

        response = client.post("/api/tiers/downgrade", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_tier"] == "freemium"

        # Verify user tier was updated
        db.refresh(user)
        assert user.subscription_tier == "freemium"

    def test_downgrade_tier_from_any_tier(self, client, db, user_token):

        """Test that downgrade works from any tier."""
        tiers_to_test = ["payg", "pro", "custom"]

        for tier in tiers_to_test:
            user = User(
                id=f"downgrade_{tier}",
                email=f"downgrade_{tier}@test.com",
                password_hash=hash_password("password123"),
                email_verified=True,
                is_admin=False,
                credits=10.0,
                subscription_tier=tier,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
        db.commit()

        for tier in tiers_to_test:
            token = user_token(f"downgrade_{tier}", f"downgrade_{tier}@test.com")
            response = client.post("/api/tiers/downgrade", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            data = response.json()
            assert data["new_tier"] == "freemium"

    def test_downgrade_tier_requires_authentication(self, client):

        """Test that downgrade requires authentication."""
        response = client.post("/api/tiers/downgrade")
        assert response.status_code == 401
