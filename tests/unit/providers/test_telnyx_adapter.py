"""Unit tests for Telnyx adapter — Issue 1 from STABILITY_CHECKLIST.md."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import httpx

from app.services.providers.telnyx_adapter import TelnyxAdapter
from app.services.providers.base_provider import PurchaseResult, MessageResult


@pytest.fixture
def adapter():
    with patch("app.services.providers.telnyx_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.telnyx_api_key = "test_key"
        s.telnyx_timeout = 30
        mock_settings.return_value = s
        return TelnyxAdapter()


@pytest.fixture
def disabled_adapter():
    with patch("app.services.providers.telnyx_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.telnyx_api_key = None
        s.telnyx_timeout = 30
        mock_settings.return_value = s
        return TelnyxAdapter()


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
    search_resp = _mock_response(
        {
            "data": [
                {
                    "phone_number": "+12025551234",
                    "cost_information": {"upfront_cost": "1.00"},
                }
            ]
        }
    )
    order_resp = _mock_response({"data": {"id": "order-abc"}})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=search_resp)
        client.post = AsyncMock(return_value=order_resp)
        mock_client_fn.return_value = client

        result = await adapter.purchase_number("whatsapp", "US", area_code="202")

    assert isinstance(result, PurchaseResult)
    assert result.phone_number == "+12025551234"
    assert result.order_id == "order-abc"
    assert result.provider == "telnyx"
    assert result.assigned_area_code == "202"
    assert result.area_code_matched is True


@pytest.mark.asyncio
async def test_purchase_number_no_inventory(adapter):
    search_resp = _mock_response({"data": []})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=search_resp)
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="No Telnyx numbers available"):
            await adapter.purchase_number("whatsapp", "GB")


@pytest.mark.asyncio
async def test_purchase_number_api_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.HTTPError("connection failed"))
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="Telnyx purchase failed"):
            await adapter.purchase_number("whatsapp", "GB")


@pytest.mark.asyncio
async def test_purchase_number_timeout(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError, match="Telnyx purchase failed"):
            await adapter.purchase_number("whatsapp", "GB")


@pytest.mark.asyncio
async def test_purchase_number_invalid_response(adapter):
    search_resp = _mock_response(
        {"data": [{"phone_number": "+12025551234", "cost_information": {}}]}
    )
    order_resp = _mock_response({"data": {}})  # Missing "id"

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=search_resp)
        client.post = AsyncMock(return_value=order_resp)
        mock_client_fn.return_value = client

        with pytest.raises(RuntimeError):
            await adapter.purchase_number("whatsapp", "US")


@pytest.mark.asyncio
async def test_purchase_number_area_code_filter(adapter):
    search_resp = _mock_response(
        {
            "data": [
                {
                    "phone_number": "+14155551234",
                    "cost_information": {"upfront_cost": "1.00"},
                }
            ]
        }
    )
    order_resp = _mock_response({"data": {"id": "order-xyz"}})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=search_resp)
        client.post = AsyncMock(return_value=order_resp)
        mock_client_fn.return_value = client

        result = await adapter.purchase_number("whatsapp", "US", area_code="415")

    # Verify area code filter was passed
    call_params = client.get.call_args[1]["params"]
    assert call_params.get("filter[national_destination_code]") == "415"
    assert result.assigned_area_code == "415"


# ── check_messages ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_messages_success(adapter):
    resp = _mock_response(
        {
            "data": [
                {"text": "Your code is 123456", "received_at": "2026-03-26T12:00:00Z"}
            ]
        }
    )

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("order-abc")

    assert len(messages) == 1
    assert isinstance(messages[0], MessageResult)
    assert messages[0].code == "123456"


@pytest.mark.asyncio
async def test_check_messages_empty(adapter):
    resp = _mock_response({"data": []})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("order-abc")

    assert messages == []


@pytest.mark.asyncio
async def test_check_messages_api_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=Exception("API error"))
        mock_client_fn.return_value = client

        messages = await adapter.check_messages("order-abc")

    assert messages == []


@pytest.mark.asyncio
async def test_check_messages_created_after_filter(adapter):
    old_time = "2026-03-26T10:00:00Z"
    new_time = "2026-03-26T12:00:00Z"
    resp = _mock_response(
        {
            "data": [
                {"text": "Old code 111111", "received_at": old_time},
                {"text": "New code 999999", "received_at": new_time},
            ]
        }
    )

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        cutoff = datetime(2026, 3, 26, 11, 0, 0, tzinfo=timezone.utc)
        messages = await adapter.check_messages("order-abc", created_after=cutoff)

    assert len(messages) == 1
    assert messages[0].code == "999999"


# ── cancel ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_success(adapter):
    resp = _mock_response({}, status_code=200)

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.delete = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        result = await adapter.cancel("order-abc")

    assert result is True


@pytest.mark.asyncio
async def test_cancel_failure(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.delete = AsyncMock(side_effect=Exception("API error"))
        mock_client_fn.return_value = client

        result = await adapter.cancel("order-abc")

    assert result is False


# ── get_balance ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_balance_success(adapter):
    resp = _mock_response({"data": {"balance": "150.75"}})

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        mock_client_fn.return_value = client

        balance = await adapter.get_balance()

    assert balance == 150.75


@pytest.mark.asyncio
async def test_get_balance_error(adapter):
    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=Exception("API error"))
        mock_client_fn.return_value = client

        balance = await adapter.get_balance()

    assert balance == 0.0


# ── _extract_code ─────────────────────────────────────────────────────────────


def test_extract_code_hyphenated(adapter):
    assert adapter._extract_code("Your code is 806-185") == "806185"


def test_extract_code_plain(adapter):
    assert adapter._extract_code("Use code 123456 to verify") == "123456"


def test_extract_code_no_match(adapter):
    assert adapter._extract_code("No code here") == ""


# ── client lifecycle ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_client_cleanup(adapter):
    mock_client = AsyncMock()
    adapter._client = mock_client

    await adapter.__aexit__(None, None, None)

    mock_client.aclose.assert_called_once()


def test_client_singleton(adapter):
    """Same client returned on repeated calls — no new connections created."""
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
    messages = await disabled_adapter.check_messages("order-abc")
    assert messages == []


@pytest.mark.asyncio
async def test_disabled_provider_cancel(disabled_adapter):
    result = await disabled_adapter.cancel("order-abc")
    assert result is False


@pytest.mark.asyncio
async def test_disabled_provider_balance(disabled_adapter):
    balance = await disabled_adapter.get_balance()
    assert balance == 0.0
