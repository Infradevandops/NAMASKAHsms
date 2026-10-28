"""Unit tests for app/services/stock_monitor.py and GET /api/services/stock."""

from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_services(entries):
    """Build a list of TV service dicts."""
    return [{"name": n, "price": p} for n, p in entries]


# ---------------------------------------------------------------------------
# build_stock_map
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_stock_map_empty_cache():
    """Returns {} when tv:services_list is not in cache."""
    from app.services.stock_monitor import build_stock_map

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        result = await build_stock_map()

    assert result == {}


@pytest.mark.asyncio
async def test_build_stock_map_available():
    """Service with price > 0 is marked available."""
    from app.services.stock_monitor import build_stock_map

    services = _make_services([("WhatsApp", "2.63"), ("Telegram", "1.80")])
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert result["whatsapp"]["available"] is True
    assert result["telegram"]["available"] is True


@pytest.mark.asyncio
async def test_build_stock_map_out_of_stock_null_price():
    """Service with price=None is marked unavailable."""
    from app.services.stock_monitor import build_stock_map

    services = _make_services([("WhatsApp", None)])
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert result["whatsapp"]["available"] is False


@pytest.mark.asyncio
async def test_build_stock_map_out_of_stock_zero_price():
    """Service with price=0 is marked unavailable."""
    from app.services.stock_monitor import build_stock_map

    services = _make_services([("Discord", "0")])
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert result["discord"]["available"] is False


@pytest.mark.asyncio
async def test_build_stock_map_slug_normalisation():
    """Service name is lowercased and spaces replaced with underscores."""
    from app.services.stock_monitor import build_stock_map

    services = _make_services([("Google Play", "2.00")])
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert "google_play" in result


@pytest.mark.asyncio
async def test_build_stock_map_skips_nameless_entries():
    """Entries with no name are silently skipped."""
    from app.services.stock_monitor import build_stock_map

    services = [{"name": "", "price": "2.00"}, {"price": "1.50"}]
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert result == {}


@pytest.mark.asyncio
async def test_build_stock_map_provider_field():
    """Every entry carries provider=textverified."""
    from app.services.stock_monitor import build_stock_map

    services = _make_services([("Uber", "2.63")])
    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=services)
        result = await build_stock_map()

    assert result["uber"]["provider"] == "textverified"


@pytest.mark.asyncio
async def test_build_stock_map_cache_exception_returns_empty():
    """Cache read exception returns {} without raising."""
    from app.services.stock_monitor import build_stock_map

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(side_effect=Exception("redis down"))
        result = await build_stock_map()

    assert result == {}


# ---------------------------------------------------------------------------
# refresh_stock_cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_stock_cache_writes_to_cache():
    """refresh_stock_cache stores a dict with services/total/available/updated_at."""
    from app.services.stock_monitor import refresh_stock_cache

    services = _make_services([("WhatsApp", "2.63"), ("Discord", None)])
    written = {}

    async def fake_get(key):
        if key == "tv:services_list":
            return services
        return None

    async def fake_set(key, value, ttl):
        written[key] = value

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(side_effect=fake_get)
        mock_cache.set = AsyncMock(side_effect=fake_set)
        await refresh_stock_cache()

    assert "services:stock" in written
    payload = written["services:stock"]
    assert payload["total"] == 2
    assert payload["available"] == 1
    assert "updated_at" in payload
    assert "services" in payload


@pytest.mark.asyncio
async def test_refresh_stock_cache_skips_write_on_empty():
    """refresh_stock_cache does not write to cache when build returns {}."""
    from app.services.stock_monitor import refresh_stock_cache

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        await refresh_stock_cache()

    mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# get_stock_map
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stock_map_returns_cached():
    """get_stock_map returns cached value without refreshing."""
    from app.services.stock_monitor import get_stock_map

    cached = {"services": {"whatsapp": {"available": True}}, "total": 1, "available": 1}

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=cached)
        result = await get_stock_map()

    assert result == cached


@pytest.mark.asyncio
async def test_get_stock_map_refreshes_when_stale():
    """get_stock_map calls refresh and returns newly written data when cache is empty."""
    from app.services.stock_monitor import get_stock_map

    services = _make_services([("Telegram", "1.80")])
    call_count = {"n": 0}

    async def fake_get(key):
        call_count["n"] += 1
        if key == "tv:services_list":
            return services
        # First call to services:stock returns None (stale), second returns data
        if call_count["n"] <= 2:
            return None
        return {
            "services": {"telegram": {"available": True}},
            "total": 1,
            "available": 1,
        }

    with patch("app.services.stock_monitor.cache") as mock_cache:
        mock_cache.get = AsyncMock(side_effect=fake_get)
        mock_cache.set = AsyncMock()
        result = await get_stock_map()

    # Should have attempted a refresh (set was called)
    mock_cache.set.assert_called_once()


# ---------------------------------------------------------------------------
# Endpoint shape — GET /api/services/stock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stock_endpoint_returns_correct_shape():
    """GET /api/services/stock returns services/available/total keys."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    payload = {
        "services": {
            "whatsapp": {"available": True, "price": "2.63", "provider": "textverified"}
        },
        "total": 1,
        "available": 1,
        "updated_at": "2026-10-26T12:00:00+00:00",
    }

    with patch(
        "app.services.stock_monitor.get_stock_map", new=AsyncMock(return_value=payload)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/services/stock")

    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert "available" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_stock_endpoint_returns_empty_on_exception():
    """GET /api/services/stock returns empty shape when get_stock_map raises."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    with patch(
        "app.services.stock_monitor.get_stock_map",
        new=AsyncMock(side_effect=Exception("boom")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/services/stock")

    assert resp.status_code == 200
    data = resp.json()
    assert data["services"] == {}
    assert data["available"] == 0
    assert data["total"] == 0
