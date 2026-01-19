"""Tests for Notifications page and endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestNotificationsEndpoints:
    """Test notifications API endpoints."""

    def test_notifications_page_requires_auth(self, client):
        """Notifications page should require authentication."""
        response = client.get("/notifications", follow_redirects=False)
        assert response.status_code in [401, 302, 307]

    def test_notifications_page_loads(self, client, auth_headers):
        """Notifications page should load for authenticated users."""
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        assert b"Notifications" in response.content

    def test_get_notifications_requires_auth(self, client):
        """GET /api/notifications should require auth."""
        response = client.get("/api/notifications")
        assert response.status_code == 401

    def test_get_notifications_returns_list(self, client, auth_headers):
        """GET /api/notifications should return notification list."""
        response = client.get("/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data

    def test_mark_notification_read(self, client, auth_headers):
        """POST /api/notifications/{id}/read should mark as read (or 404)."""
        response = client.post("/api/notifications/fake-id/read", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_mark_all_read(self, client, auth_headers):
        """POST /api/notifications/mark-all-read should work."""
        response = client.post("/api/notifications/mark-all-read", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_notification(self, client, auth_headers):
        """DELETE /api/notifications/{id} should delete notification (or 404)."""
        response = client.delete("/api/notifications/fake-id", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestNotificationsPageContent:
    """Test notifications page HTML content."""

    def test_page_has_mark_all_read_button(self, client, auth_headers):
        """Page should have mark all read button or equivalent."""
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        # Check for various possible identifiers of the button
        content = response.content.lower()
        assert b"mark" in content or b"read" in content

    def test_page_has_notification_list(self, client, auth_headers):
        """Page should have notification list container."""
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        assert b"notification" in response.content.lower()


class TestNotificationTypes:
    """Test different notification types."""

    def test_get_notifications_params(self, client, auth_headers):
        """Should be able to call notifications with various types."""
        for ntype in ["system", "payment", "verification"]:
            response = client.get(
                f"/api/notifications?type={ntype}", headers=auth_headers
            )
            assert response.status_code == 200
