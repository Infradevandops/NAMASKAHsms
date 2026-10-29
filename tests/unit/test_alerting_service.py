"""Unit tests for app/services/alerting_service.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# send_alert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_alert_returns_true_on_success():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc._send_email_alert = AsyncMock()
    result = await svc.send_alert({"type": "test", "severity": "info", "message": "hi"})
    assert result is True
    svc._send_email_alert.assert_called_once()


@pytest.mark.asyncio
async def test_send_alert_returns_false_on_exception():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc._send_email_alert = AsyncMock(side_effect=Exception("smtp down"))
    result = await svc.send_alert({"type": "test", "severity": "critical", "message": "x"})
    assert result is False


# ---------------------------------------------------------------------------
# _send_email_alert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_email_alert_drops_when_no_admin_email():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()

    mock_settings = MagicMock()
    mock_settings.effective_admin_notify_email = None

    with patch("app.services.alerting_service.AlertingService._send_email_alert",
               wraps=svc._send_email_alert):
        with patch("app.core.config.get_settings", return_value=mock_settings):
            with patch("app.services.email_service.email_service") as mock_email:
                mock_email._send = AsyncMock()
                await svc._send_email_alert({"type": "t", "severity": "info", "message": "m"})
                mock_email._send.assert_not_called()


@pytest.mark.asyncio
async def test_send_email_alert_sends_with_correct_severity_emoji():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()

    mock_settings = MagicMock()
    mock_settings.effective_admin_notify_email = "admin@vrenum.app"

    sent = {}

    async def capture(to, subject, html):
        sent["subject"] = subject

    with patch("app.core.config.get_settings", return_value=mock_settings):
        with patch("app.services.email_service.email_service") as mock_email:
            mock_email._send = AsyncMock(side_effect=capture)
            await svc._send_email_alert({"type": "revenue_zero", "severity": "critical", "message": "bad"})

    assert "🚨" in sent["subject"]
    assert "CRITICAL" in sent["subject"]


@pytest.mark.asyncio
async def test_send_email_alert_warning_emoji():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()

    mock_settings = MagicMock()
    mock_settings.effective_admin_notify_email = "admin@vrenum.app"

    sent = {}

    async def capture(to, subject, html):
        sent["subject"] = subject

    with patch("app.core.config.get_settings", return_value=mock_settings):
        with patch("app.services.email_service.email_service") as mock_email:
            mock_email._send = AsyncMock(side_effect=capture)
            await svc._send_email_alert({"type": "target_miss", "severity": "warning", "message": "miss"})

    assert "⚠️" in sent["subject"]


# ---------------------------------------------------------------------------
# check_revenue_zero
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_revenue_zero_skips_before_18():
    from app.services.alerting_service import AlertingService
    from datetime import datetime, timezone
    svc = AlertingService()

    early = datetime(2026, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.alerting_service.datetime") as mock_dt:
        mock_dt.now.return_value = early
        result = await svc.check_revenue_zero(MagicMock())

    assert result is False


@pytest.mark.asyncio
async def test_check_revenue_zero_fires_when_zero_revenue():
    from app.services.alerting_service import AlertingService
    from datetime import datetime, timezone
    svc = AlertingService()
    svc.send_alert = AsyncMock(return_value=True)

    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = 0

    after_18 = datetime(2026, 10, 26, 18, 30, 0, tzinfo=timezone.utc)
    with patch("app.services.alerting_service.datetime") as mock_dt:
        mock_dt.now.return_value = after_18
        result = await svc.check_revenue_zero(mock_db)

    assert result is True
    svc.send_alert.assert_called_once()
    call_args = svc.send_alert.call_args[0][0]
    assert call_args["severity"] == "critical"
    assert call_args["type"] == "revenue_zero"


@pytest.mark.asyncio
async def test_check_revenue_zero_no_alert_when_revenue_exists():
    from app.services.alerting_service import AlertingService
    from datetime import datetime, timezone
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = 150.0

    after_18 = datetime(2026, 10, 26, 19, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.alerting_service.datetime") as mock_dt:
        mock_dt.now.return_value = after_18
        result = await svc.check_revenue_zero(mock_db)

    assert result is False
    svc.send_alert.assert_not_called()


@pytest.mark.asyncio
async def test_check_revenue_zero_returns_false_on_db_exception():
    from app.services.alerting_service import AlertingService
    from datetime import datetime, timezone
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("db error")

    after_18 = datetime(2026, 10, 26, 18, 1, 0, tzinfo=timezone.utc)
    with patch("app.services.alerting_service.datetime") as mock_dt:
        mock_dt.now.return_value = after_18
        result = await svc.check_revenue_zero(mock_db)

    assert result is False


# ---------------------------------------------------------------------------
# process_alert_batch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_alert_batch_empty():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    result = await svc.process_alert_batch([])
    assert result == {"sent": 0, "deduplicated": 0}


@pytest.mark.asyncio
async def test_process_alert_batch_single_alert():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock(return_value=True)

    result = await svc.process_alert_batch([
        {"type": "revenue_zero", "severity": "critical", "message": "bad"}
    ])

    assert result["sent"] == 1
    assert result["deduplicated"] == 0
    svc.send_alert.assert_called_once()


@pytest.mark.asyncio
async def test_process_alert_batch_deduplicates():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock(return_value=True)

    alerts = [
        {"type": "revenue_zero", "severity": "critical", "message": "bad"},
        {"type": "revenue_zero", "severity": "critical", "message": "also bad"},
        {"type": "revenue_zero", "severity": "critical", "message": "still bad"},
    ]
    result = await svc.process_alert_batch(alerts)

    assert result["sent"] == 1
    assert result["deduplicated"] == 2
    svc.send_alert.assert_called_once()
    # Summary message should mention count
    call_msg = svc.send_alert.call_args[0][0]["message"]
    assert "3 similar alerts" in call_msg


@pytest.mark.asyncio
async def test_process_alert_batch_different_types_sent_separately():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock(return_value=True)

    alerts = [
        {"type": "revenue_zero", "severity": "critical", "message": "a"},
        {"type": "margin_low", "severity": "critical", "message": "b"},
    ]
    result = await svc.process_alert_batch(alerts)

    assert result["sent"] == 2
    assert result["deduplicated"] == 0


# ---------------------------------------------------------------------------
# send_margin_alert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_margin_alert_calls_send_alert():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    await svc.send_margin_alert(8.5, 1000.0, 915.0)

    svc.send_alert.assert_called_once()
    payload = svc.send_alert.call_args[0][0]
    assert payload["type"] == "margin_below_threshold"
    assert payload["severity"] == "critical"
    assert "8.5%" in payload["message"]
    assert "$1000.00" in payload["message"]
    assert "$915.00" in payload["message"]


@pytest.mark.asyncio
async def test_send_margin_alert_zero_margin():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    await svc.send_margin_alert(0.0, 500.0, 500.0)

    payload = svc.send_alert.call_args[0][0]
    assert "0.0%" in payload["message"]


# ---------------------------------------------------------------------------
# send_target_miss_alert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_target_miss_alert_calls_send_alert():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    await svc.send_target_miss_alert("2026-10", 2800.0, 4000.0)

    svc.send_alert.assert_called_once()
    payload = svc.send_alert.call_args[0][0]
    assert payload["type"] == "monthly_target_missed"
    assert payload["severity"] == "warning"
    assert "2026-10" in payload["message"]
    assert "$2800.00" in payload["message"]
    assert "$4000.00" in payload["message"]


@pytest.mark.asyncio
async def test_send_target_miss_alert_shortfall_correct():
    from app.services.alerting_service import AlertingService
    svc = AlertingService()
    svc.send_alert = AsyncMock()

    await svc.send_target_miss_alert("2026-10", 3000.0, 4000.0)

    payload = svc.send_alert.call_args[0][0]
    assert "$1000.00" in payload["message"]  # shortfall
