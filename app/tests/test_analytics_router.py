"""Tests for analytics router functionality."""
import pytest
from unittest.mock import Mock
from app.api.analytics import router
from app.core.dependencies import get_current_user_id


def test_analytics_router_endpoints():
    """Test that all analytics endpoints are properly defined."""
    routes = [route.path for route in router.routes]
    
    expected_routes = [
        "/analytics/usage",
        "/analytics/costs",
        "/analytics/export"
    ]
    
    for expected_route in expected_routes:
        assert expected_route in routes, f"Missing route: {expected_route}"


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return "user_123"


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


def test_get_user_analytics_structure(mock_user, mock_db):
    """Test user analytics endpoint returns correct structure."""
    from app.api.analytics import get_user_analytics
    
    # Mock database queries
    mock_db.query.return_value.filter.return_value.count.return_value = 10
    mock_db.query.return_value.filter.return_value.scalar.return_value = 50.0
    mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
    
    result = get_user_analytics(mock_user, 30, mock_db)
    
    assert hasattr(result, 'total_verifications')
    assert hasattr(result, 'success_rate')
    assert hasattr(result, 'total_spent')
    assert hasattr(result, 'popular_services')
    assert hasattr(result, 'daily_usage')


def test_cost_analysis_structure(mock_user, mock_db):
    """Test cost analysis endpoint returns correct structure."""
    from app.api.analytics import get_cost_analysis
    
    # Mock database queries
    mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.scalar.return_value = 100.0
    
    result = get_cost_analysis(mock_user, 30, mock_db)
    
    assert "service_costs" in result
    assert "monthly_spending" in result
    assert "period_days" in result


def test_export_data_verifications(mock_user, mock_db):
    """Test data export for verifications."""
    from app.api.analytics import export_data
    
    # Mock verification data
    mock_verification = Mock()
    mock_verification.id = "ver_123"
    mock_verification.service_name = "telegram"
    mock_verification.phone_number = "+1234567890"
    mock_verification.status = "completed"
    mock_verification.cost = 1.5
    mock_verification.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    mock_verification.completed_at = None
    
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_verification]
    
    result = export_data(mock_user, "verifications", "json", None, None, mock_db)
    
    assert "data" in result
    assert "format" in result
    assert "count" in result
    assert "date_range" in result


if __name__ == "__main__":
    pytest.main([__file__])