"""Tests for balance_monitor, health_check, and pvapins_adapter to hit 90% coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.providers.pvapins_adapter import PVAPinsAdapter
from app.services.providers.base_provider import PurchaseResult
from app.services.providers.provider_errors import ProviderError


# ── PVAPinsAdapter fixtures ───────────────────────────────────────────────────


@pytest.fixture
def adapter():
    with patch("app.services.providers.pvapins_adapter.get_settings") as mock_s:
        s = MagicMock()
        s.pvapins_api_key = "test_key"
        s.pvapins_timeout = 30
        mock_s.return_value = s
        return PVAPinsAdapter()


@pytest.fixture
def disabled_adapter():
    with patch("app.services.providers.pvapins_adapter.get_settings") as mock_s:
        s = MagicMock()
        s.pvapins_api_key = None
        s.pvapins_timeout = 30
        mock_s.return_value = s
        return PVAPinsAdapter()


def _mock_response(json_data, status_code=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


# ── PVAPinsAdapter: purchase_number ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_pvapins_purchase_success(adapter):
    resp = _mock_response({"code": 100, "data": "60123456789"})
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client
        result = await adapter.purchase_number("whatsapp", "MY")
    assert isinstance(result, PurchaseResult)
    assert result.phone_number == "+60123456789"
    assert result.provider == "pvapins"


@pytest.mark.asyncio
async def test_pvapins_purchase_no_inventory(adapter):
    resp = _mock_response({"code": 200, "data": "unavailable"})
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client
        with pytest.raises(ProviderError) as exc:
            await adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "no_inventory_country"


@pytest.mark.asyncio
async def test_pvapins_purchase_malformed_response(adapter):
    resp = _mock_response({"code": 999, "data": ""})
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client
        with pytest.raises(ProviderError) as exc:
            await adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "malformed_response"


@pytest.mark.asyncio
async def test_pvapins_purchase_unsupported_country(adapter):
    with pytest.raises(ProviderError) as exc:
        await adapter.purchase_number("whatsapp", "ZZ")
    assert exc.value.category == "unsupported_country"


@pytest.mark.asyncio
async def test_pvapins_purchase_disabled(disabled_adapter):
    with pytest.raises(ProviderError) as exc:
        await disabled_adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "not_configured"


@pytest.mark.asyncio
async def test_pvapins_purchase_timeout(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_fn.return_value = client
        with pytest.raises(ProviderError) as exc:
            await adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "timeout"


@pytest.mark.asyncio
async def test_pvapins_purchase_connect_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client_fn.return_value = client
        with pytest.raises(ProviderError) as exc:
            await adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "provider_unreachable"


@pytest.mark.asyncio
async def test_pvapins_purchase_http_status_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        err_resp = MagicMock()
        err_resp.status_code = 503
        client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=err_resp)
        )
        mock_client_fn.return_value = client
        with pytest.raises(ProviderError) as exc:
            await adapter.purchase_number("whatsapp", "MY")
    assert exc.value.category == "provider_unreachable"


@pytest.mark.asyncio
async def test_pvapins_purchase_with_city_sets_note(adapter):
    resp = _mock_response({"code": 100, "data": "60123456789"})
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client
        result = await adapter.purchase_number("whatsapp", "MY", city="Kuala Lumpur")
    assert result.city_honoured is False
    assert result.city_note is not None


# ── PVAPinsAdapter: other methods ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pvapins_check_messages_returns_empty(adapter):
    assert await adapter.check_messages("any_id") == []


@pytest.mark.asyncio
async def test_pvapins_report_failed_returns_false(adapter):
    assert await adapter.report_failed("any_id") is False


@pytest.mark.asyncio
async def test_pvapins_cancel_returns_false(adapter):
    assert await adapter.cancel("any_id") is False


@pytest.mark.asyncio
async def test_pvapins_get_balance_returns_zero(adapter):
    assert await adapter.get_balance() == 0.0


def test_pvapins_extract_code_hyphenated(adapter):
    assert adapter._extract_code("Code: 123-456") == "123456"


def test_pvapins_extract_code_plain(adapter):
    assert adapter._extract_code("Your OTP is 987654") == "987654"


def test_pvapins_extract_code_empty(adapter):
    assert adapter._extract_code("") == ""


@pytest.mark.asyncio
async def test_pvapins_client_cleanup(adapter):
    mock_client = AsyncMock()
    adapter._client = mock_client
    await adapter.__aexit__(None, None, None)
    mock_client.aclose.assert_called_once()


def test_pvapins_map_country_known(adapter):
    assert adapter._map_country("MY") == "malaysia"


def test_pvapins_map_country_unknown(adapter):
    assert adapter._map_country("ZZ") is None


def test_pvapins_enabled(adapter):
    assert adapter.enabled is True


def test_pvapins_name(adapter):
    assert adapter.name == "pvapins"


# ── health_check ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check_textverified_disabled():
    from app.services.providers.health_check import check_textverified_health
    with patch("app.services.providers.health_check.TextVerifiedService") as MockSvc:
        svc = MagicMock()
        svc.enabled = False
        MockSvc.return_value = svc
        result = await check_textverified_health()
    assert result["status"] == "disabled"


@pytest.mark.asyncio
async def test_health_check_textverified_ok():
    from app.services.providers.health_check import check_textverified_health
    with patch("app.services.providers.health_check.TextVerifiedService") as MockSvc:
        svc = AsyncMock()
        svc.enabled = True
        svc.get_balance = AsyncMock(return_value={"balance": 100.0})
        MockSvc.return_value = svc
        result = await check_textverified_health()
    assert result["status"] == "ok"
    assert result["balance"] == 100.0


@pytest.mark.asyncio
async def test_health_check_textverified_error():
    from app.services.providers.health_check import check_textverified_health
    with patch("app.services.providers.health_check.TextVerifiedService") as MockSvc:
        svc = AsyncMock()
        svc.enabled = True
        svc.get_balance = AsyncMock(side_effect=Exception("API down"))
        MockSvc.return_value = svc
        result = await check_textverified_health()
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_health_check_telnyx_disabled():
    from app.services.providers.health_check import check_telnyx_health
    with patch("app.services.providers.telnyx_adapter.TelnyxAdapter") as MockAdapter:
        adapter = MagicMock()
        adapter.enabled = False
        MockAdapter.return_value = adapter
        result = await check_telnyx_health()
    assert result["provider"] == "telnyx"


@pytest.mark.asyncio
async def test_health_check_fivesim_disabled():
    from app.services.providers.health_check import check_fivesim_health
    with patch("app.services.providers.fivesim_adapter.FiveSimAdapter") as MockAdapter:
        adapter = MagicMock()
        adapter.enabled = False
        MockAdapter.return_value = adapter
        result = await check_fivesim_health()
    assert result["provider"] == "5sim"


@pytest.mark.asyncio
async def test_health_check_pvapins_disabled():
    from app.services.providers.health_check import check_pvapins_health
    with patch("app.services.providers.pvapins_adapter.PVAPinsAdapter") as MockAdapter:
        adapter = MagicMock()
        adapter.enabled = False
        MockAdapter.return_value = adapter
        result = await check_pvapins_health()
    assert result["provider"] == "pvapins"
    assert result["status"] == "disabled"


@pytest.mark.asyncio
async def test_health_check_pvapins_ok():
    from app.services.providers.health_check import check_pvapins_health
    with patch("app.services.providers.pvapins_adapter.PVAPinsAdapter") as MockAdapter:
        adapter = MagicMock()
        adapter.enabled = True
        MockAdapter.return_value = adapter
        result = await check_pvapins_health()
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_run_provider_health_checks():
    from app.services.providers.health_check import run_provider_health_checks
    ok = {"status": "ok", "balance": 100.0}
    disabled = {"status": "disabled", "balance": None}
    with patch("app.services.providers.health_check.check_textverified_health", return_value=ok), \
         patch("app.services.providers.health_check.check_telnyx_health", return_value=disabled), \
         patch("app.services.providers.health_check.check_fivesim_health", return_value=disabled), \
         patch("app.services.providers.health_check.check_pvapins_health", return_value=disabled):
        results = await run_provider_health_checks()
    assert results["textverified"]["status"] == "ok"


# ── balance_monitor ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evaluate_balances_ok():
    from app.services.providers.balance_monitor import evaluate_balances
    with patch("app.services.providers.balance_monitor.get_settings"):
        await evaluate_balances({"textverified": 100.0})  # no exception


@pytest.mark.asyncio
async def test_evaluate_balances_warn():
    from app.services.providers.balance_monitor import evaluate_balances
    with patch("app.services.providers.balance_monitor.get_settings"), \
         patch("app.services.providers.balance_monitor._send_alert", new_callable=AsyncMock):
        await evaluate_balances({"textverified": 40.0})


@pytest.mark.asyncio
async def test_evaluate_balances_critical():
    from app.services.providers.balance_monitor import evaluate_balances
    with patch("app.services.providers.balance_monitor.get_settings"), \
         patch("app.services.providers.balance_monitor._send_alert", new_callable=AsyncMock):
        await evaluate_balances({"textverified": 20.0})


@pytest.mark.asyncio
async def test_evaluate_balances_disable():
    from app.services.providers.balance_monitor import evaluate_balances
    settings = MagicMock()
    with patch("app.services.providers.balance_monitor.get_settings", return_value=settings):
        await evaluate_balances({"telnyx": 5.0})
    assert settings.telnyx_enabled is False


@pytest.mark.asyncio
async def test_evaluate_balances_disable_fivesim():
    from app.services.providers.balance_monitor import evaluate_balances
    settings = MagicMock()
    with patch("app.services.providers.balance_monitor.get_settings", return_value=settings):
        await evaluate_balances({"5sim": 5.0})
    assert settings.fivesim_enabled is False


@pytest.mark.asyncio
async def test_check_all_balances():
    from app.services.providers.balance_monitor import check_all_balances
    with patch("app.services.providers.balance_monitor.ProviderRouter") as MockRouter:
        router = AsyncMock()
        router.get_provider_balances = AsyncMock(return_value={"textverified": 100.0})
        MockRouter.return_value = router
        result = await check_all_balances()
    assert result["textverified"] == 100.0


@pytest.mark.asyncio
async def test_send_alert_failure_is_swallowed():
    from app.services.providers.balance_monitor import _send_alert
    with patch("app.services.providers.balance_monitor.SessionLocal", side_effect=Exception("db down")):
        # Should not raise
        await _send_alert("telnyx", 20.0, "critical")
