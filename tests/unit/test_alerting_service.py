import pytest

from app.services.alerting_service import AlertingService


@pytest.fixture
def service():
    return AlertingService()


@pytest.mark.asyncio
async def test_send_alert_success(service, capsys):
    alert = {"message": "Test Alert", "severity": "info", "type": "test"}
    result = await service.send_alert(alert)
    assert result is True

    captured = capsys.readouterr()
    assert "📧 Email Alert: Test Alert" in captured.out
    assert "💬 Slack Alert: ℹ️ Test Alert" in captured.out
    assert "🔗 Webhook Alert: test - Test Alert" in captured.out


@pytest.mark.asyncio
async def test_process_alert_batch_dedup(service):
    alerts = [
        {"message": "A1", "severity": "warning", "type": "cpu"},
        {"message": "A2", "severity": "warning", "type": "cpu"},
        {"message": "B1", "severity": "critical", "type": "db"},
    ]

    result = await service.process_alert_batch(alerts)

    # 2 groups:
    # cpu_warning (2 items) -> 1 summary sent (+1 dedup)
    # db_critical (1 item) -> 1 sent (+0 dedup)

    assert result["sent"] == 2
    assert result["deduplicated"] == 1


@pytest.mark.asyncio
async def test_process_alert_batch_empty(service):
    result = await service.process_alert_batch([])
    assert result["sent"] == 0
    assert result["deduplicated"] == 0


@pytest.mark.asyncio
async def test_send_alert_exception(service):
    # Mock _send_email_alert to raise exception
    original_method = service._send_email_alert

    async def mock_fail(alert):
        raise ValueError("Simulated failure")

    service._send_email_alert = mock_fail

    try:
        result = await service.send_alert({"message": "Fail"})
        assert result is False
    finally:
        service._send_email_alert = original_method
