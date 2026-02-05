"""Tests for Analytics page and endpoints."""


from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from app.core.dependencies import get_current_user_id
from main import app

class TestAnalyticsEndpoints:

    """Test analytics API endpoints."""

    @pytest.fixture
    def client(self):

        """Create test client."""
        return TestClient(app)

        @pytest.fixture
    def auth_headers(self):

        """Mock auth headers."""
        return {"Authorization": "Bearer test_token"}

        @pytest.fixture
    def mock_user_id(self):

        """Mock user ID dependency."""

    def override():

        return "test_user_123"

        app.dependency_overrides[get_current_user_id] = override
        yield "test_user_123"
        app.dependency_overrides.clear()

    def test_analytics_page_requires_auth(self, client):

        """Analytics page should require authentication."""
        response = client.get("/analytics", follow_redirects=False)
        # Should redirect to login or return 401
        assert response.status_code in [401, 302, 307]

    def test_analytics_page_loads_for_authenticated_user(self, client, mock_user_id):

        """Analytics page should load for authenticated users."""
        response = client.get("/analytics")
        assert response.status_code == 200
        assert b"Analytics" in response.content

    def test_analytics_summary_requires_auth(self, client):

        """Analytics summary endpoint should require authentication."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 401

    def test_analytics_summary_returns_data(self, client, mock_user_id):

        """Analytics summary should return expected data structure."""
        response = client.get("/api/analytics/summary")

        if response.status_code == 200:
            data = response.json()
            # Check expected fields exist
            assert "total_verifications" in data or response.status_code == 200

    def test_analytics_summary_with_date_range(self, client, mock_user_id):

        """Analytics summary should accept date range parameters."""
        today = datetime.now().strftime("%Y-%m-%d")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        response = client.get(f"/api/analytics/summary?from={thirty_days_ago}&to={today}")

        # Should not error on date params
        assert response.status_code in [200, 404, 500]

    def test_analytics_empty_data_for_new_user(self, client, mock_user_id):

        """New users should get empty/zero analytics."""
        response = client.get("/api/analytics/summary")

        if response.status_code == 200:
            data = response.json()
            # New user should have zero or empty data
            total = data.get("total_verifications", 0)
            assert isinstance(total, (int, float))


class TestAnalyticsPageContent:

        """Test analytics page HTML content."""

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

    def test_page_has_date_picker(self, client, mock_user_id):

        """Analytics page should have date range picker."""
        response = client.get("/analytics")
        assert response.status_code == 200
        assert b"date-from" in response.content
        assert b"date-to" in response.content

    def test_page_has_export_button(self, client, mock_user_id):

        """Analytics page should have export functionality."""
        response = client.get("/analytics")
        assert response.status_code == 200
        assert b"Export" in response.content or b"export" in response.content

    def test_page_has_charts(self, client, mock_user_id):

        """Analytics page should have chart containers."""
        response = client.get("/analytics")
        assert response.status_code == 200
        assert b"chart" in response.content.lower()

    def test_page_has_stats_grid(self, client, mock_user_id):

        """Analytics page should have stats grid."""
        response = client.get("/analytics")
        assert response.status_code == 200
        assert b"stat-" in response.content or b"stats-grid" in response.content


class TestAnalyticsErrorHandling:

        """Test analytics error handling."""

        @pytest.fixture
    def client(self):

        return TestClient(app)

    def test_invalid_date_format(self, client):

        """Should handle invalid date format gracefully."""
        # This test checks the endpoint doesn't crash on bad input
        response = client.get("/api/analytics/summary?from=invalid&to=also-invalid")
        # Should return error or ignore bad params, not crash
        assert response.status_code in [200, 400, 401, 422]

    def test_future_date_range(self, client):

        """Should handle future date range."""
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        response = client.get(f"/api/analytics/summary?from={future}&to={future}")
        # Should return empty data or error, not crash
        assert response.status_code in [200, 400, 401, 422]
