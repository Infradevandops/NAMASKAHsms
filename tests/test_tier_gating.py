"""Tests for tier-based access control (gating).

from datetime import datetime, timezone
from app.models.user import User
from app.utils.security import hash_password

Feature: tier-system-rbac
Tests validate that tier-gated endpoints properly restrict access based on user tier.
"""


class TestPayGEndpointGating:

    """Tests for endpoints that require payg tier or higher."""

def test_freemium_user_gets_402_on_voice_verify_page(self, client, regular_user, user_token):

        """Test that freemium users get 402 when accessing /voice-verify."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/voice-verify", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_freemium_user_gets_402_on_api_docs_page(self, client, regular_user, user_token):

        """Test that freemium users get 402 when accessing /api-docs."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/api-docs", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_freemium_user_gets_402_on_affiliate_page(self, client, regular_user, user_token):

        """Test that freemium users get 402 when accessing /affiliate."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/affiliate", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_payg_user_can_access_payg_pages(self, client, db, user_token):

        """Test that payg users can access payg-tier pages."""
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

        # Test /voice-verify page
        response = client.get("/voice-verify", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402

        # Test /api-docs page
        response = client.get("/api-docs", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402

        # Test /affiliate page
        response = client.get("/affiliate", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402


class TestProEndpointGating:

    """Tests for endpoints that require pro tier or higher."""

def test_freemium_user_gets_402_on_bulk_purchase_page(self, client, regular_user, user_token):

        """Test that freemium users get 402 when accessing /bulk-purchase."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_payg_user_gets_402_on_bulk_purchase_page(self, client, db, user_token):

        """Test that payg users get 402 when accessing /bulk-purchase."""
        user = User(
            id="payg_user_bulk",
            email="payg_bulk@test.com",
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

        token = user_token("payg_user_bulk", "payg_bulk@test.com")
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_pro_user_can_access_bulk_purchase_page(self, client, db, user_token):

        """Test that pro users can access /bulk-purchase."""
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
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402


class TestCustomTierAccess:

    """Tests for custom tier access to all endpoints."""

def test_custom_user_can_access_all_pages(self, client, db, user_token):

        """Test that custom tier users can access all tier-gated pages."""
        user = User(
            id="custom_user",
            email="custom@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="custom",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = user_token("custom_user", "custom@test.com")

        # Test payg pages
        pages_payg = ["/voice-verify", "/api-docs", "/affiliate"]
for page in pages_payg:
            response = client.get(page, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code != 402, f"Custom user should access {page}"

        # Test pro pages
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402


class TestTierGatingErrorResponse:

    """Tests for 402 error response format."""

def test_402_response_includes_error_details(self, client, regular_user, user_token):

        """Test that 402 response includes error details."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/voice-verify", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

        data = response.json()
        # Should have error details (either 'detail' or 'details' or 'message')
        assert "detail" in data or "details" in data or "message" in data

def test_402_response_indicates_required_tier(self, client, regular_user, user_token):

        """Test that 402 response indicates the required tier."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/voice-verify", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

        # Response should indicate payg is required
        response_text = str(response.json())
        assert "payg" in response_text.lower() or "tier" in response_text.lower()


class TestTierHierarchyEnforcement:

    """Tests for tier hierarchy enforcement across all tiers."""

def test_tier_hierarchy_freemium_to_pro(self, client, db, user_token):

        """Test that freemium users cannot access pro features."""
        user = User(
            id="freemium_test",
            email="freemium@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="freemium",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = user_token("freemium_test", "freemium@test.com")
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_tier_hierarchy_payg_to_pro(self, client, db, user_token):

        """Test that payg users cannot access pro features."""
        user = User(
            id="payg_test",
            email="payg_test@test.com",
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

        token = user_token("payg_test", "payg_test@test.com")
        response = client.get("/bulk-purchase", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 402

def test_tier_hierarchy_pro_can_access_payg_features(self, client, db, user_token):

        """Test that pro users can access payg features."""
        user = User(
            id="pro_test",
            email="pro_test@test.com",
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

        token = user_token("pro_test", "pro_test@test.com")

        # Pro users should be able to access payg pages
        response = client.get("/voice-verify", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code != 402


class TestUnauthenticatedAccessToGatedPages:

    """Tests for unauthenticated access to tier-gated pages."""

def test_unauthenticated_user_gets_401_on_gated_pages(self, client):

        """Test that unauthenticated users get 401 on tier-gated pages."""
        pages = ["/voice-verify", "/api-docs", "/affiliate", "/bulk-purchase"]

for page in pages:
            response = client.get(page)
            assert response.status_code == 401, f"Unauthenticated user should get 401 on {page}"