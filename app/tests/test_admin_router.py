"""Tests for admin router functionality."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.api.admin import router
from app.core.dependencies import get_admin_user_id, get_db


def test_admin_router_endpoints():
    """Test that all admin endpoints are properly defined."""
    routes = [route.path for route in router.routes]
    
    expected_routes = [
        "/admin/users",
        "/admin/users/{user_id}",
        "/admin/users/{user_id}/credits",
        "/admin/users/{user_id}/suspend",
        "/admin/users/{user_id}/activate",
        "/admin/stats",
        "/admin/support/tickets",
        "/admin/support/{ticket_id}/respond",
        "/admin/verifications/active",
        "/admin/verifications/{verification_id}/cancel",
        "/admin/system/health",
        "/admin/transactions",
        "/admin/broadcast"
    ]
    
    for expected_route in expected_routes:
        assert expected_route in routes, f"Missing route: {expected_route}"


def test_admin_authentication_required():
    """Test that admin endpoints require admin authentication."""
    # All routes should have admin dependency
    for route in router.routes:
        if hasattr(route, 'dependant'):
            dependencies = [dep.call for dep in route.dependant.dependencies]
            assert get_admin_user_id in dependencies, f"Route {route.path} missing admin auth"


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing."""
    return "admin_user_123"


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


def test_get_platform_stats_structure(mock_admin_user, mock_db):
    """Test platform stats endpoint returns correct structure."""
    from app.api.admin import get_platform_stats
    
    # Mock database queries
    mock_db.query.return_value.count.return_value = 100
    mock_db.query.return_value.filter.return_value.count.return_value = 50
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.scalar.return_value = 1000.0
    
    result = get_platform_stats(mock_admin_user, 7, mock_db)
    
    assert "total_verifications" in result
    assert "success_rate" in result
    assert "total_spent" in result
    assert "popular_services" in result
    assert "daily_usage" in result


def test_system_health_endpoint(mock_admin_user, mock_db):
    """Test system health endpoint."""
    from app.api.admin import get_system_health
    
    # Mock successful database query
    mock_db.execute.return_value = None
    mock_db.query.return_value.count.return_value = 100
    mock_db.query.return_value.filter.return_value.count.return_value = 50
    
    result = get_system_health(mock_admin_user, mock_db)
    
    assert result["system_status"] == "healthy"
    assert result["database"] == "healthy"
    assert "statistics" in result
    assert "timestamp" in result


if __name__ == "__main__":
    pytest.main([__file__])