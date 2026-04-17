"""Unit tests for 5sim adapter — Issue 2 from STABILITY_CHECKLIST.md."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.providers.fivesim_adapter import FiveSimAdapter
from app.services.providers.base_provider import PurchaseResult, MessageResult


@pytest.fixture
def adapter():
    with patch("app.services.providers.fivesim_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.fivesim_api_key = "test_key"
        s.fivesim_timeout = 30
        mock_settings.return_value = s
        a = FiveSimAdapter()
        a._country_cache = {"GB": "unitedkingdom", "DE": "germany", "US": "usa"}
        a._service_cache = {"whatsapp": "whatsapp", "telegram": "telegram"}
        return a


@pytest.fixture
def disabled_adapter():
    with patch("app.services.providers.fivesim_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.fivesim_api_key = None
        s.fivesim_timeout = 30
        mock_settings.return_value = s
        return FiveSimAdapter()


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


# ── purchase_number ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_purchase_number_success(adapter):
    products_resp = _mock_response({"virtual21": {"cost": 0.5, "count": 10}})
    purchase_resp = _mock_response({"id": 12345, "phone": "447911123456", "price": 0.5})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[products_resp, purchase_resp])
        mock_client_fn.return_value = client

        result = await adapter.purchase_number("whatsapp", "GB")

    assert isinstance(result, PurchaseResult)
    assert result.phone_number == "+447911123456"
    assert result.order_id == "12345"
    assert result.provider == "5sim"
    assert result.cost == 0.5


@pytest.mark.asyncio
async def test_purchase_number_country_mapping(adapter):
    products_resp = _mock_response({"any": {"cost": 0.5, "count": 5}})
    purchase_resp = _mock_response({"id": 1, "phone": "4915123456789", "price": 0.5})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[products_resp, purchase_resp])
        mock_client_fn.return_value = client

        await adapter.purchase_number("whatsapp", "DE")

    purchase_call_url = client.get.call_args_list[1][0][0]
    assert "germany" in purchase_call_url


@pytest.mark.asyncio
async def test_purchase_number_service_mapping(adapter):
    products_resp = _mock_response({"any": {"cost": 0.5, "count": 5}})
    purchase_resp = _mock_response({"id": 1, "phone": "447911123456", "price": 0.5})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[products_resp, purchase_resp])
        mock_client_fn.return_value = client

        await adapter.purchase_number("telegram", "GB")

    purchase_call_url = client.get.call_args_list[1][0][0]
    assert "telegram" in purchase_call_url


@pytest.mark.asyncio
async def test_purchase_number_operator_selection(adapter):
    products_resp = _mock_response(
        {
            "expensive_op": {"cost": 2.0, "count": 5},
            "cheap_op": {"cost": 0.3, "count": 10},
            "no_stock": {"cost": 0.1, "count": 0},
        }
    )
    purchase_resp = _mock_response({"id": 1, "phone": "447911123456", "price": 0.3})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[products_resp, purchase_resp])
        mock_client_fn.return_value = client

        await adapter.purchase_number("whatsapp", "GB")

    purchase_call_url = client.get.call_args_list[1][0][0]
    assert "cheap_op" in purchase_call_url


@pytest.mark.asyncio
async def test_purchase_number_no_country_support(adapter):
    adapter._country_cache = {}

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=_mock_response({}))
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="does not support country"):
            await adapter.purchase_number("whatsapp", "ZZ")


@pytest.mark.asyncio
async def test_purchase_number_api_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("connection failed"))
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="5sim purchase failed"):
            await adapter.purchase_number("whatsapp", "GB")


@pytest.mark.asyncio
async def test_purchase_number_no_phone_returned(adapter):
    products_resp = _mock_response({"any": {"cost": 0.5, "count": 5}})
    purchase_resp = _mock_response({"id": 1, "price": 0.5})  # No "phone"

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[products_resp, purchase_resp])
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="did not return phone"):
            await adapter.purchase_number("whatsapp", "GB")


# ── check_messages ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_messages_received(adapter):
    resp = _mock_response(
        {
            "status": "RECEIVED",
            "sms": [
                {
                    "text": "Your code is 654321",
                    "code": "654321",
                    "created_at": "2026-03-26T12:00:00Z",
                }
            ],
        }
    )

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("12345")

    assert len(messages) == 1
    assert messages[0].code == "654321"


@pytest.mark.asyncio
async def test_check_messages_pending(adapter):
    resp = _mock_response({"status": "PENDING", "sms": []})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("12345")

    assert messages == []


@pytest.mark.asyncio
async def test_check_messages_timeout_status(adapter):
    resp = _mock_response({"status": "TIMEOUT", "sms": []})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("12345")

    assert messages == []


@pytest.mark.asyncio
async def test_check_messages_api_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("API error"))
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("12345")

    assert messages == []


# ── report_failed / cancel ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_report_failed_success(adapter):
    resp = _mock_response({"status": "CANCELED"})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        result = await adapter.report_failed("12345")

    assert result is True


@pytest.mark.asyncio
async def test_report_failed_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("API error"))
        mock_client_fn.return_value = client

        result = await adapter.report_failed("12345")

    assert result is False


# ── get_balance ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_balance_success(adapter):
    resp = _mock_response({"balance": 75.50})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        balance = await adapter.get_balance()

    assert balance == 75.50


@pytest.mark.asyncio
async def test_get_balance_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("API error"))
        mock_client_fn.return_value = client

        balance = await adapter.get_balance()

    assert balance == 0.0


# ── caching ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_map_country_cached(adapter):
    adapter._country_cache = {"GB": "unitedkingdom"}

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        mock_client_fn.return_value = client

        result = await adapter._map_country("GB")

    assert result == "unitedkingdom"
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_map_country_fallback(adapter):
    adapter._country_cache = {}
    resp = _mock_response({"someothercountry": {}})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        result = await adapter._map_country("US")

    assert result == "usa"


@pytest.mark.asyncio
async def test_map_service_cached(adapter):
    adapter._service_cache = {"whatsapp": "whatsapp"}
    result = await adapter._map_service("whatsapp")
    assert result == "whatsapp"


# ── operator selection ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_best_operator_no_inventory(adapter):
    resp = _mock_response({"op1": {"cost": 0.5, "count": 0}})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        result = await adapter._get_best_operator("unitedkingdom", "whatsapp")

    assert result == "any"


@pytest.mark.asyncio
async def test_get_best_operator_api_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("API error"))
        mock_client_fn.return_value = client

        result = await adapter._get_best_operator("unitedkingdom", "whatsapp")

    assert result == "any"


# ── _extract_code ─────────────────────────────────────────────────────────────


def test_extract_code_hyphenated(adapter):
    assert adapter._extract_code("Code: 806-185") == "806185"


def test_extract_code_plain(adapter):
    assert adapter._extract_code("Your OTP is 987654") == "987654"


# ── client lifecycle ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_client_cleanup(adapter):
    mock_client = AsyncMock()
    adapter._client = mock_client
    await adapter.__aexit__(None, None, None)
    mock_client.aclose.assert_called_once()


def test_client_singleton(adapter):
    c1 = adapter._get_client()
    c2 = adapter._get_client()
    assert c1 is c2


# ── disabled provider ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_disabled_provider_purchase(disabled_adapter):
    with pytest.raises(RuntimeError, match="not configured"):
        await disabled_adapter.purchase_number("whatsapp", "GB")


@pytest.mark.asyncio
async def test_disabled_provider_check_messages(disabled_adapter):
    assert await disabled_adapter.check_messages("12345") == []


@pytest.mark.asyncio
async def test_disabled_provider_balance(disabled_adapter):
    assert await disabled_adapter.get_balance() == 0.0
