"""Unit tests for app/services/target_tracking_service.py"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_db(target=None, user_count=10, new_users=2, active_users=3,
             tier_counts=None, snapshots=None, revenue=0.0):
    """Build a mock DB session for TargetTrackingService tests."""
    db = MagicMock()
    tier_counts = tier_counts or {"freemium": 5, "payg": 3, "pro": 1, "custom": 1}

    # execute().scalar_one_or_none() — for get_active_target
    db.execute.return_value.scalar_one_or_none.return_value = target

    # query().scalar() chain — used for counts
    def query_scalar_side_effect(*args, **kwargs):
        mock = MagicMock()
        mock.scalar.return_value = user_count
        mock.filter.return_value.scalar.return_value = new_users
        mock.filter.return_value.filter.return_value.scalar.return_value = active_users
        return mock

    db.query.side_effect = query_scalar_side_effect

    # execute().scalar() — for check_month_end_target revenue query
    db.execute.return_value.scalar.return_value = revenue

    return db


def _make_target(month="2026-10", target_count=350, revenue_target=4000.0):
    t = MagicMock()
    t.month = month
    t.target_count = target_count
    t.revenue_target = Decimal(str(revenue_target))
    t.is_active = True
    return t


# ---------------------------------------------------------------------------
# get_active_target
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_active_target_returns_existing():
    from app.services.target_tracking_service import TargetTrackingService

    existing = _make_target()
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = existing

    svc = TargetTrackingService(db)
    result = await svc.get_active_target("2026-10")

    assert result is existing
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_active_target_creates_default_when_missing():
    from app.services.target_tracking_service import TargetTrackingService

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = TargetTrackingService(db)
    result = await svc.get_active_target("2026-10")

    db.add.assert_called_once()
    db.commit.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.month == "2026-10"
    assert added.target_count == 350
    assert added.is_active is True


@pytest.mark.asyncio
async def test_get_active_target_uses_current_month_when_none_given():
    from app.services.target_tracking_service import TargetTrackingService

    existing = _make_target()
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = existing

    svc = TargetTrackingService(db)
    result = await svc.get_active_target()  # no month_str

    assert result is existing


# ---------------------------------------------------------------------------
# record_daily_snapshot
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_daily_snapshot_skips_if_exists():
    from app.services.target_tracking_service import TargetTrackingService

    db = MagicMock()
    # scalar_one_or_none returns existing snapshot
    db.execute.return_value.scalar_one_or_none.return_value = MagicMock()

    svc = TargetTrackingService(db)
    result = await svc.record_daily_snapshot()

    assert result is None
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_record_daily_snapshot_creates_when_missing():
    from app.services.target_tracking_service import TargetTrackingService

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    # query().scalar() for counts
    call_count = {"n": 0}
    def query_side(*args):
        call_count["n"] += 1
        m = MagicMock()
        m.scalar.return_value = call_count["n"] * 3
        m.filter.return_value.scalar.return_value = 2
        m.filter.return_value.filter.return_value.scalar.return_value = 1
        return m

    db.query.side_effect = query_side

    svc = TargetTrackingService(db)
    await svc.record_daily_snapshot()

    db.add.assert_called_once()
    db.commit.assert_called_once()
    snapshot = db.add.call_args[0][0]
    assert hasattr(snapshot, "snapshot_date")
    assert snapshot.snapshot_date == date.today()


# ---------------------------------------------------------------------------
# get_growth_projections
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_growth_projections_returns_expected_keys():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(target_count=350)
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = target

    # snapshots query
    snap1 = MagicMock()
    snap1.new_users = 15
    snap1.snapshot_date = date(2026, 10, 25)
    snap2 = MagicMock()
    snap2.new_users = 10
    snap2.snapshot_date = date(2026, 10, 24)

    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [snap1, snap2]
    db.query.return_value.scalar.return_value = 100

    svc = TargetTrackingService(db)
    result = await svc.get_growth_projections()

    assert "month" in result
    assert "target" in result
    assert "current" in result
    assert "percentage" in result
    assert "velocity" in result
    assert "status" in result


@pytest.mark.asyncio
async def test_get_growth_projections_on_track_when_velocity_high():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(target_count=350)
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = target

    # 14 snapshots with 15 new users each = velocity 15 >= 12 → On Track
    snaps = [MagicMock(new_users=15, snapshot_date=date(2026, 10, i+1)) for i in range(14)]
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = snaps
    db.query.return_value.scalar.return_value = 50

    svc = TargetTrackingService(db)
    result = await svc.get_growth_projections()

    assert result["status"] == "On Track"


@pytest.mark.asyncio
async def test_get_growth_projections_behind_when_velocity_low():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(target_count=350)
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = target

    snaps = [MagicMock(new_users=2, snapshot_date=date(2026, 10, i+1)) for i in range(14)]
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = snaps
    db.query.return_value.scalar.return_value = 20

    svc = TargetTrackingService(db)
    result = await svc.get_growth_projections()

    assert result["status"] == "Behind"


@pytest.mark.asyncio
async def test_get_growth_projections_no_snapshots():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(target_count=350)
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = target
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.scalar.return_value = 0

    svc = TargetTrackingService(db)
    result = await svc.get_growth_projections()

    assert result["velocity"] == 0.0
    assert result["projected_date"] is None


# ---------------------------------------------------------------------------
# check_month_end_target
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_month_end_target_fires_alert_when_below():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(revenue_target=4000.0)
    db = MagicMock()

    svc = TargetTrackingService(db)
    svc.get_active_target = AsyncMock(return_value=target)
    # Revenue query returns 2800 — below 4000
    db.execute.return_value.scalar.return_value = 2800.0

    with patch("app.services.alerting_service.alerting_service") as mock_alerting:
        mock_alerting.send_target_miss_alert = AsyncMock()
        result = await svc.check_month_end_target()

    assert result is True
    mock_alerting.send_target_miss_alert.assert_called_once()
    call_args = mock_alerting.send_target_miss_alert.call_args[0]
    assert call_args[1] == 2800.0   # actual
    assert call_args[2] == 4000.0   # target


@pytest.mark.asyncio
async def test_check_month_end_target_no_alert_when_met():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(revenue_target=4000.0)
    db = MagicMock()

    svc = TargetTrackingService(db)
    svc.get_active_target = AsyncMock(return_value=target)
    db.execute.return_value.scalar.return_value = 4500.0

    with patch("app.services.alerting_service.alerting_service") as mock_alerting:
        mock_alerting.send_target_miss_alert = AsyncMock()
        result = await svc.check_month_end_target()

    assert result is False
    mock_alerting.send_target_miss_alert.assert_not_called()


@pytest.mark.asyncio
async def test_check_month_end_target_skips_when_zero_target():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(revenue_target=0.0)
    db = MagicMock()

    svc = TargetTrackingService(db)
    svc.get_active_target = AsyncMock(return_value=target)

    with patch("app.services.alerting_service.alerting_service") as mock_alerting:
        mock_alerting.send_target_miss_alert = AsyncMock()
        result = await svc.check_month_end_target()

    assert result is False
    mock_alerting.send_target_miss_alert.assert_not_called()


@pytest.mark.asyncio
async def test_check_month_end_target_zero_revenue_fires_alert():
    from app.services.target_tracking_service import TargetTrackingService

    target = _make_target(revenue_target=4000.0)
    db = MagicMock()

    svc = TargetTrackingService(db)
    svc.get_active_target = AsyncMock(return_value=target)
    db.execute.return_value.scalar.return_value = 0.0

    with patch("app.services.alerting_service.alerting_service") as mock_alerting:
        mock_alerting.send_target_miss_alert = AsyncMock()
        result = await svc.check_month_end_target()

    assert result is True
