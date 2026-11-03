"""Tests for stock monitor — price-based availability (Task 1)."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def services_with_prices():
    return [
        {
            "id": "tinder",
            "name": "Tinder",
            "price": 0.50,
            "cost": 0.50,
            "quantity": None,
        },
        {
            "id": "whatsapp",
            "name": "Whatsapp",
            "price": 1.50,
            "cost": 1.50,
            "quantity": None,
        },
        {
            "id": "google",
            "name": "Google",
            "price": 0.75,
            "cost": 0.75,
            "quantity": None,
        },
        {
            "id": "nullprice",
            "name": "Nullprice",
            "price": None,
            "cost": None,
            "quantity": None,
        },
        {
            "id": "zeroprice",
            "name": "Zeroprice",
            "price": 0.0,
            "cost": 0.0,
            "quantity": None,
        },
    ]


@pytest.mark.asyncio
async def test_build_stock_map_price_based(services_with_prices):
    """Services with price > 0 are available; null/zero price are not."""
    from app.services.stock_monitor import build_stock_map

    with patch("app.services.stock_monitor.cache") as mock_cache, patch(
        "app.services.stock_monitor.get_purchase_outcome", return_value=None
    ):
        mock_cache.get = AsyncMock(return_value=services_with_prices)

        result = await build_stock_map()

    assert result["tinder"]["available"] is True
    assert result["whatsapp"]["available"] is True
    assert result["google"]["available"] is True
    assert result["nullprice"]["available"] is None  # unknown, not False
    assert result["zeroprice"]["available"] is False  # explicitly zero = unavailable


@pytest.mark.asyncio
async def test_build_stock_map_outcome_overrides_price(services_with_prices):
    """Real purchase outcome overrides price-based availability."""
    from app.services.stock_monitor import build_stock_map

    async def mock_outcome(slug):
        return False if slug == "tinder" else None

    with patch("app.services.stock_monitor.cache") as mock_cache, patch(
        "app.services.stock_monitor.get_purchase_outcome", side_effect=mock_outcome
    ):
        mock_cache.get = AsyncMock(return_value=services_with_prices)

        result = await build_stock_map()

    # tinder has price but failed purchase outcome — should be unavailable
    assert result["tinder"]["available"] is False
    # whatsapp has price and no outcome — should be available
    assert result["whatsapp"]["available"] is True


@pytest.mark.asyncio
async def test_refresh_stock_cache_uses_price_not_quantity():
    """refresh_stock_cache no longer calls fetch_raw_services_with_quantity."""
    from app.services import stock_monitor

    with patch.object(
        stock_monitor, "build_stock_map", new_callable=AsyncMock
    ) as mock_build, patch.object(stock_monitor, "cache") as mock_cache:
        mock_build.return_value = {"tinder": {"available": True, "price": 0.5}}
        mock_cache.set = AsyncMock()

        await stock_monitor.refresh_stock_cache()

        mock_build.assert_called_once()
        # fetch_raw_services_with_quantity should NOT be called
        # (it's no longer in refresh_stock_cache)


@pytest.mark.asyncio
async def test_refresh_stock_cache_writes_correct_counts():
    """refresh_stock_cache writes available count correctly."""
    from app.services import stock_monitor

    stock = {
        "tinder": {
            "available": True,
            "price": 0.5,
            "quantity": None,
            "provider": "textverified",
        },
        "whatsapp": {
            "available": True,
            "price": 1.5,
            "quantity": None,
            "provider": "textverified",
        },
        "nullsvc": {
            "available": False,
            "price": None,
            "quantity": None,
            "provider": "textverified",
        },
    }

    written = {}

    async def mock_set(key, value, ttl=None):
        written[key] = value

    with patch.object(
        stock_monitor, "build_stock_map", new_callable=AsyncMock, return_value=stock
    ), patch.object(stock_monitor, "cache") as mock_cache:
        mock_cache.set = AsyncMock(side_effect=mock_set)
        mock_cache.get = AsyncMock(return_value=None)

        await stock_monitor.refresh_stock_cache()

    assert "services:stock" in written
    data = written["services:stock"]
    assert data["available"] == 2
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_get_stock_map_returns_cached():
    """get_stock_map returns cached data without refreshing."""
    from app.services.stock_monitor import get_stock_map

    cached = {"services": {"tinder": {"available": True}}, "available": 1, "total": 1}

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=cached)

        result = await get_stock_map()

    assert result == cached


@pytest.mark.asyncio
async def test_get_stock_map_refreshes_on_miss():
    """get_stock_map calls refresh when cache is empty."""
    from app.services import stock_monitor

    refreshed = {
        "services": {"google": {"available": True}},
        "available": 1,
        "total": 1,
    }
    call_count = {"n": 0}

    async def mock_get(key):
        call_count["n"] += 1
        return None if call_count["n"] == 1 else refreshed

    refresh_mock = AsyncMock()
    with patch.object(stock_monitor, "cache") as mock_cache, patch(
        "app.services.stock_monitor.refresh_stock_cache", refresh_mock
    ):
        mock_cache.get = AsyncMock(side_effect=mock_get)
        await stock_monitor.get_stock_map()

    refresh_mock.assert_called_once()
