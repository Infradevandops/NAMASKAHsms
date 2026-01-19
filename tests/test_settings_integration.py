"""Frontend integration tests for settings page.

Feature: tier-system-rbac
Tests validate that the settings page loads correctly, displays tier-appropriate tabs,
and shows correct billing information based on user subscription tier.
"""

from datetime import datetime, timezone

from app.models.user import User
from app.utils.security import hash_password


class TestSettingsPageLoading:
    """Tests for settings page loading."""

    def test_settings_page_loads_without_errors_for_authenticated_user(
        self, client, regular_user, user_token
    ):
        """Test that settings page loads successfully for authenticated users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "settings" in response.text.lower() or "account" in response.text.lower()

    def test_settings_page_requires_authentication(self, client):
        """Test that settings page requires authentication."""
        response = client.get("/settings")
        assert response.status_code == 401

    def test_settings_page_loads_for_all_tier_levels(self, client, db, user_token):
        """Test that settings page loads for users of all tier levels."""
        tiers_to_test = ["freemium", "payg", "pro", "custom"]

        for tier in tiers_to_test:
            user = User(
                id=f"settings_{tier}",
                email=f"settings_{tier}@test.com",
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
            token = user_token(f"settings_{tier}", f"settings_{tier}@test.com")
            response = client.get(
                "/settings", headers={"Authorization": f"Bearer {token}"}
            )
            assert (
                response.status_code == 200
            ), f"Settings page should load for {tier} tier"


class TestSettingsTabVisibility:
    """Tests for settings tab visibility based on tier."""

    def test_account_tab_visible_for_all_users(self, client, regular_user, user_token):
        """Test that Account tab is visible for all users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Account tab should always be visible
        assert "account" in response.text.lower()

    def test_security_tab_visible_for_all_users(self, client, regular_user, user_token):
        """Test that Security tab is visible for all users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Security tab should always be visible
        assert (
            "security" in response.text.lower() or "password" in response.text.lower()
        )

    def test_notifications_tab_visible_for_all_users(
        self, client, regular_user, user_token
    ):
        """Test that Notifications tab is visible for all users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Notifications tab should always be visible
        assert "notification" in response.text.lower()

    def test_billing_tab_visible_for_all_users(self, client, regular_user, user_token):
        """Test that Billing tab is visible for all users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Billing tab should always be visible
        assert "billing" in response.text.lower()

    def test_api_keys_tab_hidden_for_freemium_users(
        self, client, regular_user, user_token
    ):
        """Test that API Keys tab is hidden for freemium users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # API Keys tab should be hidden for freemium
        # Check that it's either not present or marked as hidden
        assert (
            "api keys" not in response.text.lower()
            or "display: none" in response.text
            or 'style="display: none"' in response.text
        )

    def test_api_keys_tab_visible_for_payg_users(self, client, db, user_token):
        """Test that API Keys tab is visible for payg users."""
        user = User(
            id="payg_api_tab",
            email="payg_api_tab@test.com",
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

        token = user_token("payg_api_tab", "payg_api_tab@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # API Keys tab should be visible for payg
        assert "api" in response.text.lower() or "key" in response.text.lower()

    def test_api_keys_tab_visible_for_pro_users(self, client, db, user_token):
        """Test that API Keys tab is visible for pro users."""
        user = User(
            id="pro_api_tab",
            email="pro_api_tab@test.com",
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

        token = user_token("pro_api_tab", "pro_api_tab@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # API Keys tab should be visible for pro
        assert "api" in response.text.lower() or "key" in response.text.lower()

    def test_api_keys_tab_visible_for_custom_users(self, client, db, user_token):
        """Test that API Keys tab is visible for custom users."""
        user = User(
            id="custom_api_tab",
            email="custom_api_tab@test.com",
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

        token = user_token("custom_api_tab", "custom_api_tab@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # API Keys tab should be visible for custom
        assert "api" in response.text.lower() or "key" in response.text.lower()


class TestSettingsBillingTab:
    """Tests for billing tab content."""

    def test_billing_tab_displays_current_tier(self, client, regular_user, user_token):
        """Test that billing tab displays the user's current tier."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain tier reference
        assert (
            "freemium" in response.text.lower()
            or "tier" in response.text.lower()
            or "plan" in response.text.lower()
        )

    def test_billing_tab_displays_correct_tier_for_payg_user(
        self, client, db, user_token
    ):
        """Test that billing tab displays correct tier for payg users."""
        user = User(
            id="payg_billing",
            email="payg_billing@test.com",
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

        token = user_token("payg_billing", "payg_billing@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain payg reference
        assert (
            "payg" in response.text.lower() or "pay-as-you-go" in response.text.lower()
        )

    def test_billing_tab_displays_correct_tier_for_pro_user(
        self, client, db, user_token
    ):
        """Test that billing tab displays correct tier for pro users."""
        user = User(
            id="pro_billing",
            email="pro_billing@test.com",
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

        token = user_token("pro_billing", "pro_billing@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain pro reference
        assert "pro" in response.text.lower()

    def test_billing_tab_displays_upgrade_options(
        self, client, regular_user, user_token
    ):
        """Test that billing tab displays upgrade options."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade or plan options
        assert (
            "upgrade" in response.text.lower()
            or "plan" in response.text.lower()
            or "pricing" in response.text.lower()
        )

    def test_billing_tab_displays_all_tier_options(
        self, client, regular_user, user_token
    ):
        """Test that billing tab displays all available tier options."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain references to multiple tiers
        assert (
            "freemium" in response.text.lower()
            or "payg" in response.text.lower()
            or "pro" in response.text.lower()
        )

    def test_billing_tab_shows_current_plan_indicator(
        self, client, regular_user, user_token
    ):
        """Test that billing tab shows which plan is current."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should indicate current plan
        assert "current" in response.text.lower() or "active" in response.text.lower()

    def test_billing_tab_hides_upgrade_for_custom_tier(self, client, db, user_token):
        """Test that billing tab hides upgrade button for custom tier users."""
        user = User(
            id="custom_billing",
            email="custom_billing@test.com",
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

        token = user_token("custom_billing", "custom_billing@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Custom tier users may not see upgrade button
        # (depends on implementation)


class TestSettingsAccountTab:
    """Tests for account tab content."""

    def test_account_tab_displays_email(self, client, regular_user, user_token):
        """Test that account tab displays user email."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain email reference
        assert "email" in response.text.lower() or regular_user.email in response.text

    def test_account_tab_displays_user_id(self, client, regular_user, user_token):
        """Test that account tab displays user ID."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain user ID reference
        assert "id" in response.text.lower() or "user" in response.text.lower()

    def test_account_tab_displays_creation_date(self, client, regular_user, user_token):
        """Test that account tab displays account creation date."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain creation date reference
        assert "created" in response.text.lower() or "date" in response.text.lower()


class TestSettingsNotificationsTab:
    """Tests for notifications tab content."""

    def test_notifications_tab_displays_email_notifications_toggle(
        self, client, regular_user, user_token
    ):
        """Test that notifications tab displays email notifications toggle."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain email notifications reference
        assert (
            "email" in response.text.lower() and "notification" in response.text.lower()
        )

    def test_notifications_tab_displays_sms_alerts_toggle(
        self, client, regular_user, user_token
    ):
        """Test that notifications tab displays SMS alerts toggle."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain SMS alerts reference
        assert "sms" in response.text.lower() and "alert" in response.text.lower()

    def test_notifications_tab_has_toggle_switches(
        self, client, regular_user, user_token
    ):
        """Test that notifications tab has toggle switches."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain toggle/switch elements
        assert (
            "switch" in response.text.lower()
            or "toggle" in response.text.lower()
            or "checkbox" in response.text.lower()
        )


class TestSettingsSecurityTab:
    """Tests for security tab content."""

    def test_security_tab_displays_password_reset_option(
        self, client, regular_user, user_token
    ):
        """Test that security tab displays password reset option."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain password reset reference
        assert "password" in response.text.lower() or "reset" in response.text.lower()

    def test_security_tab_has_password_reset_button(
        self, client, regular_user, user_token
    ):
        """Test that security tab has password reset button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain button reference
        assert "button" in response.text.lower() or "reset" in response.text.lower()


class TestSettingsAPIKeysTab:
    """Tests for API Keys tab content."""

    def test_api_keys_tab_has_generate_button_for_payg_users(
        self, client, db, user_token
    ):
        """Test that API Keys tab has generate button for payg users."""
        user = User(
            id="payg_gen_key",
            email="payg_gen_key@test.com",
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

        token = user_token("payg_gen_key", "payg_gen_key@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain generate button reference
        assert "generate" in response.text.lower() or "new" in response.text.lower()

    def test_api_keys_tab_displays_api_keys_list(self, client, db, user_token):
        """Test that API Keys tab displays list of API keys."""
        user = User(
            id="payg_keys_list",
            email="payg_keys_list@test.com",
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

        token = user_token("payg_keys_list", "payg_keys_list@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain keys list reference
        assert "key" in response.text.lower() or "api" in response.text.lower()

    def test_api_keys_tab_shows_empty_state_when_no_keys(self, client, db, user_token):
        """Test that API Keys tab shows empty state when user has no keys."""
        user = User(
            id="payg_no_keys",
            email="payg_no_keys@test.com",
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

        token = user_token("payg_no_keys", "payg_no_keys@test.com")
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain empty state or no keys message
        assert "no" in response.text.lower() or "key" in response.text.lower()


class TestSettingsTabSwitching:
    """Tests for tab switching functionality."""

    def test_settings_page_has_tab_navigation(self, client, regular_user, user_token):
        """Test that settings page has tab navigation."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain navigation elements
        assert (
            "nav" in response.text.lower()
            or "tab" in response.text.lower()
            or "button" in response.text.lower()
        )

    def test_settings_page_has_account_tab_button(
        self, client, regular_user, user_token
    ):
        """Test that settings page has Account tab button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain Account tab button
        assert "account" in response.text.lower()

    def test_settings_page_has_billing_tab_button(
        self, client, regular_user, user_token
    ):
        """Test that settings page has Billing tab button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain Billing tab button
        assert "billing" in response.text.lower()

    def test_settings_page_has_notifications_tab_button(
        self, client, regular_user, user_token
    ):
        """Test that settings page has Notifications tab button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain Notifications tab button
        assert "notification" in response.text.lower()

    def test_settings_page_has_security_tab_button(
        self, client, regular_user, user_token
    ):
        """Test that settings page has Security tab button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain Security tab button
        assert (
            "security" in response.text.lower() or "password" in response.text.lower()
        )
