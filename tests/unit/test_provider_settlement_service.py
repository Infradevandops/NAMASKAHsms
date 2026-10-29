"""Unit tests for app/services/provider_settlement_service.py"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# check_margin
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_margin_healthy_margin_no_alert():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 1000.0  # platform revenue

    svc = ProviderSettlementService(db)

    with patch("app.services.textverified_service.TextVerifiedService") as MockTV:
        MockTV.return_value.get_balance = AsyncMock(return_value={"balance": 200.0})
        with patch("app.core.cache.get_redis") as mock_redis:
            r = MagicMock()
            r.get.return_value = b"800.0"   # balance_week_start — cost = 800-200 = 600
            mock_redis.return_value = r
            with patch("app.services.alerting_service.alerting_service") as mock_alert:
                mock_alert.send_margin_alert = AsyncMock()
                result = await svc.check_margin(db)

    # margin = (1000 - 600) / 1000 * 100 = 40% — above 15%
    assert result["margin_pct"] == pytest.approx(40.0)
    assert result["alert_fired"] is False
    mock_alert.send_margin_alert.assert_not_called()


@pytest.mark.asyncio
async def test_check_margin_low_margin_fires_alert():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 1000.0

    svc = ProviderSettlementService(db)

    with patch("app.services.textverified_service.TextVerifiedService") as MockTV:
        MockTV.return_value.get_balance = AsyncMock(return_value={"balance": 50.0})
        with patch("app.core.cache.get_redis") as mock_redis:
            r = MagicMock()
            r.get.return_value = b"1000.0"  # cost = 1000-50 = 950 → margin = 5%
            mock_redis.return_value = r
            with patch("app.services.alerting_service.alerting_service") as mock_alert:
                mock_alert.send_margin_alert = AsyncMock()
                result = await svc.check_margin(db)

    assert result["margin_pct"] == pytest.approx(5.0)
    assert result["alert_fired"] is True
    mock_alert.send_margin_alert.assert_called_once()
    call_args = mock_alert.send_margin_alert.call_args[0]
    assert call_args[0] == pytest.approx(5.0)   # margin_pct
    assert call_args[1] == pytest.approx(1000.0) # revenue
    assert call_args[2] == pytest.approx(950.0)  # tv_cost


@pytest.mark.asyncio
async def test_check_margin_no_revenue_no_alert():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0.0

    svc = ProviderSettlementService(db)

    with patch("app.services.textverified_service.TextVerifiedService") as MockTV:
        MockTV.return_value.get_balance = AsyncMock(return_value={"balance": 100.0})
        with patch("app.core.cache.get_redis") as mock_redis:
            r = MagicMock()
            r.get.return_value = None  # no cached start balance
            mock_redis.return_value = r
            with patch("app.services.alerting_service.alerting_service") as mock_alert:
                mock_alert.send_margin_alert = AsyncMock()
                result = await svc.check_margin(db)

    assert result["alert_fired"] is False
    assert result["margin_pct"] == pytest.approx(100.0)  # default when no revenue
    mock_alert.send_margin_alert.assert_not_called()


@pytest.mark.asyncio
async def test_check_margin_redis_unavailable_still_runs():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 500.0

    svc = ProviderSettlementService(db)

    with patch("app.services.textverified_service.TextVerifiedService") as MockTV:
        MockTV.return_value.get_balance = AsyncMock(return_value={"balance": 100.0})
        with patch("app.core.cache.get_redis", return_value=None):
            with patch("app.services.alerting_service.alerting_service") as mock_alert:
                mock_alert.send_margin_alert = AsyncMock()
                result = await svc.check_margin(db)

    # tv_cost = 0 (no redis), margin = 100%
    assert result["tv_cost"] == 0.0
    assert result["platform_revenue"] == pytest.approx(500.0)


@pytest.mark.asyncio
async def test_check_margin_stores_balance_snapshot_in_redis():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 800.0

    svc = ProviderSettlementService(db)

    with patch("app.services.textverified_service.TextVerifiedService") as MockTV:
        MockTV.return_value.get_balance = AsyncMock(return_value={"balance": 300.0})
        with patch("app.core.cache.get_redis") as mock_redis:
            r = MagicMock()
            r.get.return_value = None
            mock_redis.return_value = r
            with patch("app.services.alerting_service.alerting_service") as mock_alert:
                mock_alert.send_margin_alert = AsyncMock()
                await svc.check_margin(db)

    # Should have stored the current balance as the new week start
    r.setex.assert_called_once_with("tv:balance_week_start", 7 * 86400, "300.0")


# ---------------------------------------------------------------------------
# create_settlement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_settlement_success():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    svc = ProviderSettlementService(db)

    result = await svc.create_settlement(
        provider_id="textverified",
        period="2026-10",
        total_messages=100,
        successful_messages=95,
        per_message_cost=1.46,
    )

    assert result["status"] == "success"
    assert result["provider_id"] == "textverified"
    assert result["total_messages"] == 100
    assert result["total_cost"] == pytest.approx(100 * 1.46 * 1.05, rel=1e-3)
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_settlement_december_period():
    """December period should roll over to January correctly."""
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    svc = ProviderSettlementService(db)

    result = await svc.create_settlement(
        provider_id="textverified",
        period="2026-12",
        total_messages=50,
        successful_messages=50,
        per_message_cost=1.46,
    )

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_create_settlement_rollback_on_error():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.commit.side_effect = Exception("db error")
    svc = ProviderSettlementService(db)

    with pytest.raises(Exception):
        await svc.create_settlement("tv", "2026-10", 10, 10, 1.46)

    db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# track_daily_costs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_track_daily_costs_success():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    svc = ProviderSettlementService(db)

    result = await svc.track_daily_costs(
        provider_id="textverified",
        messages_sent=200,
        successful_sends=190,
        per_message_rate=1.46,
    )

    assert result["status"] == "success"
    assert result["daily_cost"] == pytest.approx(200 * 1.46)
    assert result["success_rate"] == pytest.approx(95.0)
    db.add.assert_called_once()


@pytest.mark.asyncio
async def test_track_daily_costs_zero_messages():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    svc = ProviderSettlementService(db)

    result = await svc.track_daily_costs("tv", 0, 0, 1.46)

    assert result["success_rate"] == 0
    assert result["daily_cost"] == 0.0


# ---------------------------------------------------------------------------
# get_settlement_summary
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_settlement_summary_empty():
    from app.services.provider_settlement_service import ProviderSettlementService

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    svc = ProviderSettlementService(db)

    result = await svc.get_settlement_summary("textverified", 2026)

    assert result["total_messages"] == 0
    assert result["total_cost"] == 0
    assert result["periods"] == 0


@pytest.mark.asyncio
async def test_get_settlement_summary_aggregates_correctly():
    from app.services.provider_settlement_service import ProviderSettlementService

    s1 = MagicMock()
    s1.total_messages_sent = 100
    s1.total_cost = 150.0
    s1.paid_amount = 150.0
    s1.delivery_rate = 95.0

    s2 = MagicMock()
    s2.total_messages_sent = 200
    s2.total_cost = 300.0
    s2.paid_amount = 300.0
    s2.delivery_rate = 98.0

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [s1, s2]
    svc = ProviderSettlementService(db)

    result = await svc.get_settlement_summary("textverified", 2026)

    assert result["total_messages"] == 300
    assert result["total_cost"] == pytest.approx(450.0)
    assert result["outstanding_balance"] == pytest.approx(0.0)
    assert result["periods"] == 2
