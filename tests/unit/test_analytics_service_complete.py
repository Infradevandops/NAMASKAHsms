"""Unit tests for analytics service"""
import pytest
from datetime import datetime, timedelta
from app.services.analytics_service import AnalyticsService

@pytest.fixture
def analytics_service():
    return AnalyticsService()

@pytest.fixture
def mock_verifications():
    """Mock verification data"""
    return [
        {'status': 'completed', 'cost': 2.50, 'service': 'telegram', 'created_at': datetime.now()},
        {'status': 'completed', 'cost': 2.50, 'service': 'whatsapp', 'created_at': datetime.now()},
        {'status': 'failed', 'cost': 2.50, 'service': 'telegram', 'created_at': datetime.now()},
        {'status': 'pending', 'cost': 2.50, 'service': 'discord', 'created_at': datetime.now()},
    ]

def test_calculate_summary_stats(analytics_service, mock_verifications):
    """Test summary statistics calculation"""
    stats = analytics_service.calculate_summary(mock_verifications)
    
    assert stats['total_verifications'] == 4
    assert stats['successful_verifications'] == 2
    assert stats['failed_verifications'] == 1
    assert stats['pending_verifications'] == 1
    assert stats['success_rate'] == 50.0
    assert stats['total_spent'] == 10.0

def test_group_by_service(analytics_service, mock_verifications):
    """Test grouping verifications by service"""
    grouped = analytics_service.group_by_service(mock_verifications)
    
    assert 'telegram' in grouped
    assert 'whatsapp' in grouped
    assert grouped['telegram']['count'] == 2
    assert grouped['whatsapp']['count'] == 1

def test_calculate_daily_stats(analytics_service, mock_verifications):
    """Test daily statistics calculation"""
    daily = analytics_service.calculate_daily_stats(mock_verifications, days=7)
    
    assert len(daily) <= 7
    assert all('date' in day and 'count' in day for day in daily)

def test_get_top_services(analytics_service, mock_verifications):
    """Test getting top services by usage"""
    top = analytics_service.get_top_services(mock_verifications, limit=3)
    
    assert len(top) <= 3
    assert top[0]['name'] == 'telegram'  # Most used
    assert top[0]['count'] == 2
