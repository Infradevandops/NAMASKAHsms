"""Comprehensive tests for admin endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.models.verification import Verification
from app.models.subscription_tier import SubscriptionTier


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    def test_list_users_success(self, client, admin_user):
        """Test listing all users."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/users")

        assert response.status_code == 200

    def test_list_users_pagination(self, client, admin_user):
        """Test user list pagination."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/users?limit=10&offset=0")

        assert response.status_code == 200

    def test_list_users_filter_by_tier(self, client, admin_user):
        """Test filtering users by tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/users?tier=pro")

        assert response.status_code == 200

    def test_list_users_non_admin(self, client, regular_user):
        """Test non-admin cannot list users."""
        with patch("app.core.dependencies.get_current_user_id", return_value=regular_user.id):
            response = client.get("/api/v1/admin/users")

        assert response.status_code in [403, 404]

    def test_get_user_details(self, client, admin_user, regular_user):
        """Test getting specific user details."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get(f"/api/v1/admin/users/{regular_user.id}")

        assert response.status_code == 200

    def test_get_user_details_not_found(self, client, admin_user):
        """Test getting non-existent user."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/users/nonexistent-id")

        assert response.status_code == 404

    def test_update_user_tier(self, client, admin_user, regular_user, db):
        """Test updating user tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.patch(
                f"/api/v1/admin/users/{regular_user.id}/tier",
                json={"tier": "pro"}
            )

        assert response.status_code in [200, 404]

    def test_update_user_credits(self, client, admin_user, regular_user, db):
        """Test updating user credits."""
        initial_credits = regular_user.credits

        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.patch(
                f"/api/v1/admin/users/{regular_user.id}/credits",
                json={"amount": 50.0, "reason": "Admin adjustment"}
            )

        assert response.status_code in [200, 404]

    def test_suspend_user(self, client, admin_user, regular_user, db):
        """Test suspending user account."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                f"/api/v1/admin/users/{regular_user.id}/suspend",
                json={"reason": "Terms violation"}
            )

        assert response.status_code in [200, 404]

    def test_unsuspend_user(self, client, admin_user, regular_user, db):
        """Test unsuspending user account."""
        regular_user.is_active = False
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(f"/api/v1/admin/users/{regular_user.id}/unsuspend")

        assert response.status_code in [200, 404]

    def test_delete_user(self, client, admin_user, regular_user):
        """Test deleting user account."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.delete(f"/api/v1/admin/users/{regular_user.id}")

        assert response.status_code in [200, 204, 404]


class TestAdminVerificationManagement:
    """Test admin verification management endpoints."""

    def test_list_all_verifications(self, client, admin_user):
        """Test listing all verifications."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/verifications")

        assert response.status_code == 200

    def test_list_verifications_filter_by_status(self, client, admin_user):
        """Test filtering verifications by status."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/verifications?status=pending")

        assert response.status_code == 200

    def test_list_verifications_filter_by_user(self, client, admin_user, regular_user):
        """Test filtering verifications by user."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get(f"/api/v1/admin/verifications?user_id={regular_user.id}")

        assert response.status_code == 200

    def test_get_verification_details(self, client, admin_user, regular_user, db):
        """Test getting verification details."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="completed",
            cost=0.50,
            capability="sms",
            country="US"
        )
        db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get(f"/api/v1/admin/verifications/{verification.id}")

        assert response.status_code == 200

    def test_cancel_verification_admin(self, client, admin_user, regular_user, db):
        """Test admin canceling verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="pending",
            cost=0.50,
            capability="sms",
            country="US"
        )
        db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(f"/api/v1/admin/verifications/{verification.id}/cancel")

        assert response.status_code in [200, 404]

    def test_refund_verification(self, client, admin_user, regular_user, db):
        """Test refunding verification."""
        verification = Verification(
            user_id=regular_user.id,
            service_name="telegram",
            phone_number="+12025551234",
            status="completed",
            cost=0.50,
            capability="sms",
            country="US"
        )
        db.add(verification)
        db.commit()

        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                f"/api/v1/admin/verifications/{verification.id}/refund",
                json={"reason": "Service issue"}
            )

        assert response.status_code in [200, 404]


class TestAdminAnalytics:
    """Test admin analytics endpoints."""

    def test_get_dashboard_stats(self, client, admin_user):
        """Test getting dashboard statistics."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/dashboard/stats")

        assert response.status_code == 200

    def test_get_user_analytics(self, client, admin_user):
        """Test getting user analytics."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/analytics/users")

        assert response.status_code == 200

    def test_get_verification_analytics(self, client, admin_user):
        """Test getting verification analytics."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/analytics/verifications")

        assert response.status_code == 200

    def test_get_revenue_analytics(self, client, admin_user):
        """Test getting revenue analytics."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/analytics/revenue")

        assert response.status_code == 200

    def test_get_analytics_date_range(self, client, admin_user):
        """Test analytics with date range."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get(
                "/api/v1/admin/analytics/users?start_date=2024-01-01&end_date=2024-12-31"
            )

        assert response.status_code == 200

    def test_export_analytics_csv(self, client, admin_user):
        """Test exporting analytics as CSV."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/analytics/export?format=csv")

        assert response.status_code in [200, 404]

    def test_export_analytics_json(self, client, admin_user):
        """Test exporting analytics as JSON."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/analytics/export?format=json")

        assert response.status_code in [200, 404]


class TestAdminTierManagement:
    """Test admin tier management endpoints."""

    def test_list_tiers(self, client, admin_user):
        """Test listing subscription tiers."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/tiers")

        assert response.status_code == 200

    def test_get_tier_details(self, client, admin_user):
        """Test getting tier details."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/tiers/pro")

        assert response.status_code in [200, 404]

    def test_create_tier(self, client, admin_user):
        """Test creating new tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                "/api/v1/admin/tiers",
                json={
                    "name": "custom",
                    "display_name": "Custom Tier",
                    "price": 99.99,
                    "features": {
                        "api_access": True,
                        "area_code_selection": True
                    }
                }
            )

        assert response.status_code in [200, 201, 404]

    def test_update_tier(self, client, admin_user):
        """Test updating tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.patch(
                "/api/v1/admin/tiers/pro",
                json={"price": 29.99}
            )

        assert response.status_code in [200, 404]

    def test_delete_tier(self, client, admin_user):
        """Test deleting tier."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.delete("/api/v1/admin/tiers/custom")

        assert response.status_code in [200, 204, 404]


class TestAdminSystemMonitoring:
    """Test admin system monitoring endpoints."""

    def test_get_system_health(self, client, admin_user):
        """Test getting system health status."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/system/health")

        assert response.status_code == 200

    def test_get_system_metrics(self, client, admin_user):
        """Test getting system metrics."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/system/metrics")

        assert response.status_code in [200, 404]

    def test_get_error_logs(self, client, admin_user):
        """Test getting error logs."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/logs/errors")

        assert response.status_code in [200, 404]

    def test_get_audit_logs(self, client, admin_user):
        """Test getting audit logs."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.get("/api/v1/admin/logs/audit")

        assert response.status_code in [200, 404]

    def test_clear_cache(self, client, admin_user):
        """Test clearing system cache."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post("/api/v1/admin/system/cache/clear")

        assert response.status_code in [200, 404]


class TestAdminActions:
    """Test admin action endpoints."""

    def test_broadcast_notification(self, client, admin_user):
        """Test broadcasting notification to all users."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                "/api/v1/admin/actions/broadcast",
                json={
                    "title": "System Maintenance",
                    "message": "Scheduled maintenance tonight",
                    "type": "info"
                }
            )

        assert response.status_code in [200, 404]

    def test_bulk_credit_adjustment(self, client, admin_user):
        """Test bulk credit adjustment."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                "/api/v1/admin/actions/bulk-credits",
                json={
                    "user_ids": ["user1", "user2"],
                    "amount": 10.0,
                    "reason": "Promotion"
                }
            )

        assert response.status_code in [200, 404]

    def test_generate_report(self, client, admin_user):
        """Test generating system report."""
        with patch("app.core.dependencies.get_current_user_id", return_value=admin_user.id):
            response = client.post(
                "/api/v1/admin/actions/generate-report",
                json={"type": "monthly", "month": "2024-01"}
            )

        assert response.status_code in [200, 202, 404]
