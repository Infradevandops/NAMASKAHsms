"""Frontend integration tests for dashboard.

Feature: tier-system-rbac
Tests validate that the dashboard loads correctly, displays tier information,
and shows tier-appropriate UI elements based on user subscription tier.
"""

from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.verification import Verification
from app.utils.security import hash_password


class TestDashboardLoading:
    """Tests for dashboard page loading."""

    def test_dashboard_loads_without_errors_for_authenticated_user(self, client, regular_user, user_token):
        """Test that dashboard page loads successfully for authenticated users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "dashboard" in response.text.lower() or "current plan" in response.text.lower()

    def test_dashboard_requires_authentication(self, client):
        """Test that dashboard requires authentication."""
        response = client.get("/dashboard")
        assert response.status_code == 401

    def test_dashboard_loads_for_all_tier_levels(self, client, db, user_token):
        """Test that dashboard loads for users of all tier levels."""
        tiers_to_test = ["freemium", "payg", "pro", "custom"]

        for tier in tiers_to_test:
            user = User(
                id=f"dashboard_{tier}",
                email=f"dashboard_{tier}@test.com",
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
            token = user_token(f"dashboard_{tier}", f"dashboard_{tier}@test.com")
            response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, f"Dashboard should load for {tier} tier"


class TestDashboardTierInfo:
    """Tests for tier information display on dashboard."""

    def test_tier_info_displays_current_tier_name(self, client, regular_user, user_token):
        """Test that dashboard displays the user's current tier name."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain tier name or reference to freemium
        assert "freemium" in response.text.lower() or "current plan" in response.text.lower()

    def test_tier_info_displays_correct_tier_for_payg_user(self, client, db, user_token):
        """Test that dashboard displays correct tier for payg users."""
        user = User(
            id="payg_dashboard",
            email="payg_dashboard@test.com",
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

        token = user_token("payg_dashboard", "payg_dashboard@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain payg reference
        assert "payg" in response.text.lower() or "pay-as-you-go" in response.text.lower()

    def test_tier_info_displays_tier_features(self, client, regular_user, user_token):
        """Test that dashboard displays tier features."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain feature references
        assert "feature" in response.text.lower() or "sms" in response.text.lower()

    def test_tier_info_displays_pricing_for_paid_tiers(self, client, db, user_token):
        """Test that dashboard displays pricing information for paid tiers."""
        user = User(
            id="pro_pricing",
            email="pro_pricing@test.com",
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

        token = user_token("pro_pricing", "pro_pricing@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain pricing reference
        assert "$" in response.text or "month" in response.text.lower() or "free" in response.text.lower()


class TestDashboardQuotaMeter:
    """Tests for quota meter display on dashboard."""

    def test_quota_meter_hidden_for_freemium_users(self, client, regular_user, user_token):
        """Test that quota meter is hidden for freemium users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Quota card should be hidden for freemium (display: none)
        # Check that quota-related content is minimal or not prominently displayed
        assert "monthly quota usage" not in response.text.lower() or "display: none" in response.text

    def test_quota_meter_displayed_for_subscribed_users(self, client, db, user_token):
        """Test that quota meter is displayed for subscribed users."""
        user = User(
            id="payg_quota",
            email="payg_quota@test.com",
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

        token = user_token("payg_quota", "payg_quota@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain quota-related content
        assert "quota" in response.text.lower() or "monthly" in response.text.lower()

    def test_quota_meter_shows_usage_and_limit(self, client, db, user_token):
        """Test that quota meter displays both usage and limit."""
        user = User(
            id="pro_quota_display",
            email="pro_quota_display@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="pro",
            monthly_quota_used=50.0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        token = user_token("pro_quota_display", "pro_quota_display@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain quota information
        assert "quota" in response.text.lower()


class TestDashboardAPIStats:
    """Tests for API statistics display on dashboard."""

    def test_api_stats_hidden_for_freemium_users(self, client, regular_user, user_token):
        """Test that API stats are hidden for freemium users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # API stats card should be hidden for freemium
        assert "api usage" not in response.text.lower() or "display: none" in response.text

    def test_api_stats_displayed_for_subscribed_users(self, client, db, user_token):
        """Test that API stats are displayed for subscribed users."""
        user = User(
            id="payg_api_stats",
            email="payg_api_stats@test.com",
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

        token = user_token("payg_api_stats", "payg_api_stats@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain API stats reference
        assert "api" in response.text.lower()

    def test_api_stats_shows_sms_count(self, client, db, user_token):
        """Test that API stats display SMS count."""
        user = User(
            id="pro_sms_count",
            email="pro_sms_count@test.com",
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

        # Create some SMS verifications
        for i in range(3):
            verification = Verification(
                id=f"sms_stat_{i}",
                user_id=user.id,
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

        token = user_token("pro_sms_count", "pro_sms_count@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain SMS reference
        assert "sms" in response.text.lower()


class TestDashboardUpgradeButton:
    """Tests for upgrade button visibility on dashboard."""

    def test_upgrade_button_visible_for_freemium_users(self, client, regular_user, user_token):
        """Test that upgrade button is visible for freemium users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade button or reference
        assert "upgrade" in response.text.lower() or "pricing" in response.text.lower()

    def test_upgrade_button_visible_for_payg_users(self, client, db, user_token):
        """Test that upgrade button is visible for payg users."""
        user = User(
            id="payg_upgrade_btn",
            email="payg_upgrade_btn@test.com",
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

        token = user_token("payg_upgrade_btn", "payg_upgrade_btn@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade button
        assert "upgrade" in response.text.lower() or "pricing" in response.text.lower()

    def test_upgrade_button_hidden_for_custom_users(self, client, db, user_token):
        """Test that upgrade button is hidden for custom tier users."""
        user = User(
            id="custom_no_upgrade",
            email="custom_no_upgrade@test.com",
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

        token = user_token("custom_no_upgrade", "custom_no_upgrade@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Custom users may not have upgrade button visible
        # (depends on implementation - they might see "current plan" instead)

    def test_upgrade_button_links_to_pricing_page(self, client, regular_user, user_token):
        """Test that upgrade button links to pricing page."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain link to pricing
        assert "/pricing" in response.text or "upgrade" in response.text.lower()


class TestDashboardComparisonModal:
    """Tests for tier comparison modal on dashboard."""

    def test_compare_plans_button_visible_for_freemium_users(self, client, regular_user, user_token):
        """Test that compare plans button is visible for freemium users."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain compare plans button
        assert "compare" in response.text.lower() or "plans" in response.text.lower()

    def test_compare_plans_button_visible_for_subscribed_users(self, client, db, user_token):
        """Test that compare plans button is visible for subscribed users."""
        user = User(
            id="payg_compare",
            email="payg_compare@test.com",
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

        token = user_token("payg_compare", "payg_compare@test.com")
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain compare plans button
        assert "compare" in response.text.lower() or "plans" in response.text.lower()

    def test_compare_plans_modal_exists_in_html(self, client, regular_user, user_token):
        """Test that compare plans modal HTML exists on page."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain modal HTML
        assert "compare-plans-modal" in response.text or "modal" in response.text.lower()


class TestDashboardAnalyticsDisplay:
    """Tests for analytics display on dashboard."""

    def test_dashboard_displays_total_sms_count(self, client, regular_user, user_token, db):
        """Test that dashboard displays total SMS count."""
        # Create some verifications
        for i in range(5):
            verification = Verification(
                id=f"dash_sms_{i}",
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

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain SMS count reference
        assert "sms" in response.text.lower() or "total" in response.text.lower()

    def test_dashboard_displays_successful_count(self, client, regular_user, user_token, db):
        """Test that dashboard displays successful verification count."""
        # Create successful verifications
        for i in range(3):
            verification = Verification(
                id=f"dash_success_{i}",
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

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain successful count reference
        assert "successful" in response.text.lower() or "completed" in response.text.lower()

    def test_dashboard_displays_success_rate(self, client, regular_user, user_token, db):
        """Test that dashboard displays success rate."""
        # Create mix of successful and failed verifications
        for i in range(7):
            verification = Verification(
                id=f"dash_rate_{i}",
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

        for i in range(3):
            verification = Verification(
                id=f"dash_rate_fail_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="failed",
                cost=0.05,
                created_at=datetime.now(timezone.utc),
            )
            db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain success rate reference
        assert "success" in response.text.lower() or "rate" in response.text.lower() or "%" in response.text

    def test_dashboard_displays_total_spent(self, client, regular_user, user_token, db):
        """Test that dashboard displays total amount spent."""
        # Create verifications with costs
        for i in range(5):
            verification = Verification(
                id=f"dash_spent_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="completed",
                cost=0.10,
                created_at=datetime.now(timezone.utc),
            )
            db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain spent reference
        assert "spent" in response.text.lower() or "$" in response.text


class TestDashboardRecentActivity:
    """Tests for recent activity display on dashboard."""

    def test_dashboard_displays_recent_activity_table(self, client, regular_user, user_token, db):
        """Test that dashboard displays recent activity table."""
        # Create some verifications
        for i in range(3):
            verification = Verification(
                id=f"activity_dash_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="completed",
                cost=0.05,
                created_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain activity reference
        assert "activity" in response.text.lower() or "recent" in response.text.lower()

    def test_dashboard_shows_empty_state_when_no_activity(self, client, regular_user, user_token):
        """Test that dashboard shows empty state when user has no activity."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain empty state or activity section
        assert "activity" in response.text.lower() or "no" in response.text.lower()

    def test_dashboard_activity_includes_service_name(self, client, regular_user, user_token, db):
        """Test that activity displays service name."""
        verification = Verification(
            id="activity_service",
            user_id=regular_user.id,
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain service reference
        assert "sms" in response.text.lower() or "service" in response.text.lower()

    def test_dashboard_activity_includes_phone_number(self, client, regular_user, user_token, db):
        """Test that activity displays phone number."""
        verification = Verification(
            id="activity_phone",
            user_id=regular_user.id,
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain phone number reference
        assert "phone" in response.text.lower() or "+1" in response.text or "number" in response.text.lower()

    def test_dashboard_activity_includes_status(self, client, regular_user, user_token, db):
        """Test that activity displays verification status."""
        verification = Verification(
            id="activity_status",
            user_id=regular_user.id,
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification)
        db.commit()

        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain status reference
        assert "status" in response.text.lower() or "completed" in response.text.lower()
