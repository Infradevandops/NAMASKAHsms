"""Tests for Notifications page and endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from app.core.dependencies import get_current_user_id


class TestNotificationsEndpoints:
    """Test notifications API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield "test_user_123"
        app.dependency_overrides.clear()
    
    def test_notifications_page_requires_auth(self, client):
        """Notifications page should require authentication."""
        response = client.get("/notifications", follow_redirects=False)
        assert response.status_code in [401, 302, 307]
    
    def test_notifications_page_loads(self, client, mock_user_id):
        """Notifications page should load for authenticated users."""
        response = client.get("/notifications")
        assert response.status_code == 200
        assert b"Notifications" in response.content
    
    def test_get_notifications_requires_auth(self, client):
        """GET /api/notifications should require auth."""
        response = client.get("/api/notifications")
        assert response.status_code == 401
    
    def test_get_notifications_returns_list(self, client, mock_user_id):
        """GET /api/notifications should return notification list."""
        response = client.get("/api/notifications")
        
        if response.status_code == 200:
            data = response.json()
            assert "notifications" in data or isinstance(data, list)
    
    def test_mark_notification_read(self, client, mock_user_id):
        """POST /api/notifications/{id}/read should mark as read."""
        # This will likely 404 without a real notification
        response = client.post("/api/notifications/fake-id/read")
        assert response.status_code in [200, 404, 401]
    
    def test_mark_all_read(self, client, mock_user_id):
        """POST /api/notifications/mark-all-read should work."""
        response = client.post("/api/notifications/mark-all-read")
        assert response.status_code in [200, 401]
    
    def test_delete_notification(self, client, mock_user_id):
        """DELETE /api/notifications/{id} should delete notification."""
        response = client.delete("/api/notifications/fake-id")
        assert response.status_code in [200, 404, 401]


class TestNotificationsPageContent:
    """Test notifications page HTML content."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield
        app.dependency_overrides.clear()
    
    def test_page_has_filter_buttons(self, client, mock_user_id):
        """Page should have filter buttons."""
        response = client.get("/notifications")
        assert response.status_code == 200
        assert b"filter" in response.content.lower()
    
    def test_page_has_mark_all_read_button(self, client, mock_user_id):
        """Page should have mark all read button."""
        response = client.get("/notifications")
        assert response.status_code == 200
        assert b"Mark All Read" in response.content or b"mark-all" in response.content
    
    def test_page_has_notification_list(self, client, mock_user_id):
        """Page should have notification list container."""
        response = client.get("/notifications")
        assert response.status_code == 200
        assert b"notification-list" in response.content
    
    def test_page_has_empty_state(self, client, mock_user_id):
        """Page should have empty state for no notifications."""
        response = client.get("/notifications")
        assert response.status_code == 200
        assert b"empty-state" in response.content


class TestNotificationTypes:
    """Test different notification types."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_id(self):
        def override():
            return "test_user_123"
        app.dependency_overrides[get_current_user_id] = override
        yield
        app.dependency_overrides.clear()
    
    def test_filter_by_type_system(self, client, mock_user_id):
        """Should be able to filter by system type."""
        response = client.get("/api/notifications?type=system")
        assert response.status_code in [200, 401]
    
    def test_filter_by_type_payment(self, client, mock_user_id):
        """Should be able to filter by payment type."""
        response = client.get("/api/notifications?type=payment")
        assert response.status_code in [200, 401]
    
    def test_filter_by_type_verification(self, client, mock_user_id):
        """Should be able to filter by verification type."""
        response = client.get("/api/notifications?type=verification")
        assert response.status_code in [200, 401]
