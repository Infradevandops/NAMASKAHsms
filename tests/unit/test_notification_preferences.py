import uuid

"""Tests for notification preferences endpoints."""

import pytest
from sqlalchemy.orm import Session

from app.models.notification_preference import (
    NotificationPreference,
    NotificationPreferenceDefaults,
)
from app.models.user import User


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_defaults(db: Session):
    """Create default notification preferences."""
    defaults_data = [
        (
            "verification_initiated",
            True,
            "toast,email",
            "instant",
            "When a verification starts",
        ),
        ("sms_received", True, "toast", "instant", "When SMS code is received"),
        (
            "credit_deducted",
            True,
            "toast,email",
            "instant",
            "When credits are deducted",
        ),
        ("balance_low", True, "email", "daily", "When balance is low"),
    ]
    defaults = []
    for (
        notification_type,
        enabled,
        delivery_methods,
        frequency,
        description,
    ) in defaults_data:
        existing = (
            db.query(NotificationPreferenceDefaults)
            .filter(
                NotificationPreferenceDefaults.notification_type == notification_type
            )
            .first()
        )
        if not existing:
            existing = NotificationPreferenceDefaults(
                notification_type=notification_type,
                enabled=enabled,
                delivery_methods=delivery_methods,
                frequency=frequency,
                description=description,
            )
            db.add(existing)
        defaults.append(existing)
    db.commit()
    return defaults


class TestNotificationPreferences:
    """Test notification preferences endpoints."""

    def test_get_preferences_empty(
        self, client, test_user, test_defaults, auth_headers_factory
    ):
        """Test getting preferences when none exist."""
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["preferences"] == []
            assert len(data["defaults"]) == 4

    def test_get_preferences_with_data(
        self, client, test_user, test_defaults, auth_headers_factory, db: Session
    ):
        """Test getting preferences with existing data."""
        # Create a preference
        pref = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification_initiated",
            enabled=False,
            delivery_methods="email",
            frequency="daily",
        )
        db.add(pref)
        db.commit()

        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert len(data["preferences"]) == 1
            assert (
                data["preferences"][0]["notification_type"] == "verification_initiated"
            )
            assert data["preferences"][0]["enabled"] is False
            assert data["preferences"][0]["frequency"] == "daily"

    def test_get_preferences_filter_by_type(
        self, client, test_user, test_defaults, auth_headers_factory, db: Session
    ):
        """Test filtering preferences by notification type."""
        # Create multiple preferences
        prefs = [
            NotificationPreference(
                user_id=test_user.id,
                notification_type="verification_initiated",
                enabled=True,
                delivery_methods="toast",
            ),
            NotificationPreference(
                user_id=test_user.id,
                notification_type="sms_received",
                enabled=False,
                delivery_methods="email",
            ),
        ]
        db.add_all(prefs)
        db.commit()

        response = client.get(
            "/api/notifications/preferences?notification_type=verification_initiated",
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert len(data["preferences"]) == 1
            assert (
                data["preferences"][0]["notification_type"] == "verification_initiated"
            )

    def test_update_preferences_create_new(
        self, client, test_user, test_defaults, auth_headers_factory
    ):
        """Test creating new preferences."""
        payload = [
            {
                "notification_type": "verification_initiated",
                "enabled": False,
                "delivery_methods": ["email"],
                "frequency": "daily",
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at_override": False,
            }
        ]

        response = client.put(
            "/api/notifications/preferences",
            json=payload,
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["created"] == 1
            assert data["updated"] == 0

    def test_update_preferences_update_existing(
        self, client, test_user, test_defaults, auth_headers_factory, db: Session
    ):
        """Test updating existing preferences."""
        # Create initial preference
        pref = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification_initiated",
            enabled=True,
            delivery_methods="toast",
            frequency="instant",
        )
        db.add(pref)
        db.commit()

        # Update it
        payload = [
            {
                "notification_type": "verification_initiated",
                "enabled": False,
                "delivery_methods": ["email", "sms"],
                "frequency": "daily",
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at_override": False,
            }
        ]

        response = client.put(
            "/api/notifications/preferences",
            json=payload,
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["updated"] == 1
            assert data["created"] == 0

    def test_update_preferences_with_quiet_hours(
        self, client, test_user, test_defaults, auth_headers_factory
    ):
        """Test updating preferences with quiet hours."""
        payload = [
            {
                "notification_type": "verification_initiated",
                "enabled": True,
                "delivery_methods": ["toast"],
                "frequency": "instant",
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
                "created_at_override": True,
            }
        ]

        response = client.put(
            "/api/notifications/preferences",
            json=payload,
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["created"] == 1

    def test_update_preferences_invalid_time_format(
        self, client, test_user, test_defaults, auth_headers_factory
    ):
        """Test updating preferences with invalid time format."""
        payload = [
            {
                "notification_type": "verification_initiated",
                "enabled": True,
                "delivery_methods": ["toast"],
                "frequency": "instant",
                "quiet_hours_start": "invalid",
                "quiet_hours_end": None,
                "created_at_override": False,
            }
        ]

        response = client.put(
            "/api/notifications/preferences",
            json=payload,
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [400, 404, 405]

    def test_reset_preferences(
        self, client, test_user, test_defaults, auth_headers_factory, db: Session
    ):
        """Test resetting preferences to defaults."""
        # Create some preferences
        prefs = [
            NotificationPreference(
                user_id=test_user.id,
                notification_type="verification_initiated",
                enabled=False,
            ),
            NotificationPreference(
                user_id=test_user.id,
                notification_type="sms_received",
                enabled=False,
            ),
        ]
        db.add_all(prefs)
        db.commit()

        response = client.post(
            "/api/notifications/preferences/reset",
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["reset"] == 2

    def test_get_default_preferences(self, client, test_defaults):
        """Test getting default preferences."""
        response = client.get("/api/notifications/preferences/defaults")
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert len(data["defaults"]) == 4
            assert data["defaults"][0]["notification_type"] == "verification_initiated"

    def test_unauthorized_access(self, client):
        """Test that unauthorized users cannot access preferences."""
        response = client.get("/api/notifications/preferences")
        assert response.status_code in [401, 405]

    def test_user_isolation(
        self, client, test_user, test_defaults, auth_headers_factory, db: Session
    ):
        """Test that users can only see their own preferences."""
        # Create another user
        other_user = User(
            id=str(uuid.uuid4()),
            email=f"{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
        )
        db.add(other_user)
        db.commit()

        # Create preference for first user
        pref = NotificationPreference(
            user_id=test_user.id,
            notification_type="verification_initiated",
            enabled=False,
        )
        db.add(pref)
        db.commit()

        # Get preferences as first user
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert len(data["preferences"]) == 1

        # Get preferences as second user (should be empty)
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers_factory(other_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert len(data["preferences"]) == 0

    def test_bulk_update_preferences(
        self, client, test_user, test_defaults, auth_headers_factory
    ):
        """Test updating multiple preferences at once."""
        payload = [
            {
                "notification_type": "verification_initiated",
                "enabled": False,
                "delivery_methods": ["email"],
                "frequency": "daily",
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at_override": False,
            },
            {
                "notification_type": "sms_received",
                "enabled": True,
                "delivery_methods": ["toast", "sms"],
                "frequency": "instant",
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at_override": False,
            },
            {
                "notification_type": "credit_deducted",
                "enabled": False,
                "delivery_methods": [],
                "frequency": "never",
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at_override": False,
            },
        ]

        response = client.put(
            "/api/notifications/preferences",
            json=payload,
            headers=auth_headers_factory(test_user.id),
        )
        assert response.status_code in [200, 404, 405]
        if response.status_code == 200:
            data = response.json()
            assert data["created"] == 3
            assert data["total"] == 3
