from unittest.mock import MagicMock, patch

import pytest

from app.services.monitoring_service import MonitoringService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service():
    return MonitoringService()


@pytest.mark.asyncio
async def test_collect_system_metrics(service, mock_db):
    # Mock db.query(...).filter(...).count()
    # Logic:
    # 1. total_requests
    # 2. successful
    # 3. failed

    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.count.side_effect = [100, 95, 5]  # Total, Success, Failed

    with patch("app.services.monitoring_service.get_db", return_value=iter([mock_db])):
        metrics = await service.collect_system_metrics()

    assert metrics["requests"]["total"] == 100
    assert metrics["requests"]["successful"] == 95
    assert metrics["requests"]["failed"] == 5
    assert metrics["requests"]["success_rate"] == 95.0
    assert metrics["requests"]["error_rate"] == 5.0

    assert metrics["performance"]["avg_response_time"] == 850.5
    assert metrics["system"]["memory_usage"] == 85.2


@pytest.mark.asyncio
async def test_check_alerts_no_alerts(service):
    # Mock metrics to be good
    mock_metrics = {
        "performance": {"p95_response_time": 100},
        "requests": {"error_rate": 0.0, "success_rate": 100.0},
    }

    with patch.object(service, "collect_system_metrics", return_value=mock_metrics):
        alerts = await service.check_alerts()
        assert len(alerts) == 0


@pytest.mark.asyncio
async def test_check_alerts_triggered(service):
    # Mock metrics to trigger all
    mock_metrics = {
        "performance": {"p95_response_time": 5000},  # > 2000
        "requests": {"error_rate": 10.0, "success_rate": 80.0},  # > 5.0, < 95.0
    }

    with patch.object(service, "collect_system_metrics", return_value=mock_metrics):
        alerts = await service.check_alerts()
        assert len(alerts) == 3
        types = [a["type"] for a in alerts]
        assert "performance" in types
        assert "reliability" in types


@pytest.mark.asyncio
async def test_generate_health_report(service):
    # Mock metrics & alerts
    mock_metrics = {
        "requests": {"error_rate": 2.0},
        "performance": {"p95_response_time": 1600},
    }
    mock_alerts = [{"type": "warning"}]

    with (
        patch.object(service, "collect_system_metrics", return_value=mock_metrics),
        patch.object(service, "check_alerts", return_value=mock_alerts),
    ):

        report = await service.generate_health_report()

        # Calculation:
        # Initial 100
        # error_rate > 1: -20 -> 80
        # p95 > 1500: -15 -> 65
        # alerts > 0: -10 * 1 -> 55

        assert report["health_score"] == 55
        assert report["health_status"] == "unhealthy"
        assert report["sla_compliance"]["response_time_sla"] is True  # 1600 < 2000
