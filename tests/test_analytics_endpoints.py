"""Tests for analytics endpoints.

from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.verification import Verification
from app.utils.security import hash_password
from tests.conftest import create_test_token

Feature: tier-system-rbac
Tests validate analytics summary and dashboard activity endpoints.
"""


class TestAnalyticsSummaryEndpoint:

    """Tests for GET /api/analytics/summary endpoint."""

def test_analytics_summary_returns_correct_fields(self, client, regular_user):

        """Test that /api/analytics/summary returns all required fields."""
        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        required_fields = {
            "total_verifications",
            "successful_verifications",
            "failed_verifications",
            "pending_verifications",
            "success_rate",
            "total_spent",
            "average_cost",
            "recent_activity",
            "monthly_verifications",
            "monthly_spent",
            "last_updated",
        }

        assert all(field in data for field in required_fields)

def test_analytics_summary_with_no_verifications(self, client, regular_user):

        """Test analytics summary when user has no verifications."""
        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["total_verifications"] == 0
        assert data["successful_verifications"] == 0
        assert data["success_rate"] == 0
        assert data["total_spent"] == 0

def test_analytics_summary_calculates_success_rate(self, client, regular_user, db):

        """Test that success rate is calculated correctly."""
        # Create verifications with different statuses
for i in range(10):
            status = "completed" if i < 7 else "failed"
            verification = Verification(
                id=f"verify_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status=status,
                cost=0.05,
                created_at=datetime.now(timezone.utc),
            )
            db.add(verification)
        db.commit()

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["total_verifications"] == 10
        assert data["successful_verifications"] == 7
        assert data["failed_verifications"] == 3
        # Success rate is returned as decimal (0.7) not percentage (70.0)
        assert data["success_rate"] == 0.7

def test_analytics_summary_counts_monthly_verifications(self, client, regular_user, db):

        """Test that monthly verifications are counted correctly."""
        # Create verifications in current month
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

for i in range(5):
            verification = Verification(
                id=f"monthly_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="completed",
                cost=0.05,
                created_at=current_month + timedelta(days=i),
            )
            db.add(verification)

        # Create verification from previous month (should not be counted)
        old_verification = Verification(
            id="old_verify",
            user_id=regular_user.id,
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=current_month - timedelta(days=1),
        )
        db.add(old_verification)
        db.commit()

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["monthly_verifications"] == 5

def test_analytics_summary_requires_authentication(self, client):

        """Test that analytics summary requires authentication."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 401

def test_analytics_summary_with_different_user_tiers(self, client, db):

        """Test analytics summary with different user tiers."""
        tiers_to_test = ["freemium", "payg", "pro", "custom"]

for tier in tiers_to_test:
            user = User(
                id=f"analytics_{tier}",
                email=f"analytics_{tier}@test.com",
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
            token = create_test_token(f"analytics_{tier}", f"analytics_{tier}@test.com")
            response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            data = response.json()
            assert "total_verifications" in data


class TestDashboardActivityEndpoint:

    """Tests for GET /api/dashboard/activity/recent endpoint."""

def test_activity_recent_returns_array(self, client, regular_user):

        """Test that /api/dashboard/activity/recent returns an array."""
        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

def test_activity_recent_returns_activities(self, client, regular_user, db):

        """Test that activity endpoint returns recent activities."""
        # Create some verifications
for i in range(5):
            verification = Verification(
                id=f"activity_{i}",
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

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 5

def test_activity_recent_includes_required_fields(self, client, regular_user, db):

        """Test that each activity includes required fields."""
        verification = Verification(
            id="activity_test",
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

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        activity = data[0]
        required_fields = {"id", "service_name", "phone_number", "status", "created_at"}
        assert all(field in activity for field in required_fields)

def test_activity_recent_limits_to_ten(self, client, regular_user, db):

        """Test that activity endpoint limits results to 10."""
        # Create 15 verifications
for i in range(15):
            verification = Verification(
                id=f"limit_test_{i}",
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

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 10

def test_activity_recent_orders_by_created_at(self, client, regular_user, db):

        """Test that activities are ordered by created_at descending."""
        # Create verifications with specific timestamps
        base_time = datetime.now(timezone.utc)
for i in range(3):
            verification = Verification(
                id=f"order_test_{i}",
                user_id=regular_user.id,
                phone_number=f"+1234567890{i}",
                country="US",
                service_name="sms",
                capability="sms",
                status="completed",
                cost=0.05,
                created_at=base_time - timedelta(hours=i),
            )
            db.add(verification)
        db.commit()

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        # Most recent should be first
        assert data[0]["id"] == "order_test_0"
        assert data[1]["id"] == "order_test_1"
        assert data[2]["id"] == "order_test_2"

def test_activity_recent_only_returns_user_activities(self, client, regular_user, db):

        """Test that activity endpoint only returns current user's activities."""
        # Create verification for regular user
        verification1 = Verification(
            id="user1_activity",
            user_id=regular_user.id,
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification1)

        # Create verification for different user
        other_user = User(
            id="other_user",
            email="other@test.com",
            password_hash=hash_password("password123"),
            email_verified=True,
            is_admin=False,
            credits=10.0,
            subscription_tier="freemium",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(other_user)
        db.commit()

        verification2 = Verification(
            id="user2_activity",
            user_id="other_user",
            phone_number="+1234567890",
            country="US",
            service_name="sms",
            capability="sms",
            status="completed",
            cost=0.05,
            created_at=datetime.now(timezone.utc),
        )
        db.add(verification2)
        db.commit()

        token = create_test_token(regular_user.id, regular_user.email)
        response = client.get(
            "/api/dashboard/activity/recent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        # Should only have 1 activity (for regular_user)
        assert len(data) == 1
        assert data[0]["id"] == "user1_activity"

def test_activity_recent_requires_authentication(self, client):

        """Test that activity endpoint requires authentication."""
        response = client.get("/api/dashboard/activity/recent")
        assert response.status_code == 401

def test_activity_recent_with_different_user_tiers(self, client, db):

        """Test activity endpoint with different user tiers."""
        tiers_to_test = ["freemium", "payg", "pro", "custom"]

for tier in tiers_to_test:
            user = User(
                id=f"activity_{tier}",
                email=f"activity_{tier}@test.com",
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
            token = create_test_token(f"activity_{tier}", f"activity_{tier}@test.com")
            response = client.get(
                "/api/dashboard/activity/recent",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)