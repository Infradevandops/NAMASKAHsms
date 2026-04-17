"""City filtering tests — CITY_COUNTRY_FILTERING.md acceptance criteria."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.base_provider import PurchaseResult
from app.services.providers.provider_errors import ProviderError
from app.services.providers.provider_router import ProviderRouter
from app.services.providers.city_to_area_code import lookup


def _result(
    provider="textverified", phone="+12025551234", city_honoured=True, city_note=None
):
    return PurchaseResult(
        phone_number=phone,
        order_id="order-1",
        cost=2.22,
        expires_at="2026-04-13T12:00:00Z",
        provider=provider,
        city_honoured=city_honoured,
        city_note=city_note,
    )


# ── city_to_area_code ─────────────────────────────────────────────────────────


def test_us_city_translates_to_area_codes():
    assert lookup("New York") == ["212", "646", "718", "917", "929"]
    assert lookup("new york") == ["212", "646", "718", "917", "929"]  # case-insensitive
    assert lookup("Los Angeles") == ["213", "310", "323", "424", "747", "818"]
    assert lookup("Chicago") == ["312", "773", "872"]
    assert lookup("Boston") == ["339", "617", "857"]


def test_unknown_city_returns_empty():
    assert lookup("Atlantis") == []
    assert lookup("") == []
    assert lookup(None) == []


# ── provider router routing decisions ────────────────────────────────────────


def test_us_always_routes_textverified():
    router = ProviderRouter()
    with patch.object(router, "_get_textverified") as mock_tv:
        mock_tv.return_value.name = "textverified"
        provider, city_attempted, _ = router.get_provider(
            "US", city="New York", user_tier="freemium"
        )
    assert provider.name == "textverified"


def test_international_city_pro_routes_telnyx():
    router = ProviderRouter()
    with patch.object(router, "_get_telnyx") as mock_telnyx, patch.object(
        router, "_pvapins_covers", return_value=False
    ):
        mock_telnyx.return_value.name = "telnyx"
        mock_telnyx.return_value.enabled = True
        provider, city_attempted, pre_note = router.get_provider(
            "GB", city="London", user_tier="pro"
        )
    assert provider.name == "telnyx"
    assert city_attempted is True
    assert pre_note is None


def test_international_city_payg_routes_fivesim_city_dropped():
    router = ProviderRouter()
    with patch.object(router, "_get_fivesim") as mock_5sim, patch.object(
        router, "_pvapins_covers", return_value=False
    ):
        mock_5sim.return_value.name = "5sim"
        mock_5sim.return_value.enabled = True
        provider, city_attempted, pre_note = router.get_provider(
            "GB", city="London", user_tier="payg"
        )
    assert provider.name == "5sim"
    assert city_attempted is False
    assert pre_note is not None
    assert "Pro tier" in pre_note


def test_international_no_city_routes_fivesim():
    router = ProviderRouter()
    with patch.object(router, "_get_fivesim") as mock_5sim, patch.object(
        router, "_pvapins_covers", return_value=False
    ):
        mock_5sim.return_value.name = "5sim"
        mock_5sim.return_value.enabled = True
        provider, city_attempted, _ = router.get_provider(
            "DE", city=None, user_tier="payg"
        )
    assert provider.name == "5sim"
    assert city_attempted is False


# ── telnyx city retry pattern ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_telnyx_empty_city_retries_without_city():
    """When Telnyx has no inventory for city, it retries without city and returns a number."""
    from app.services.providers.telnyx_adapter import TelnyxAdapter
    import httpx

    with patch("app.services.providers.telnyx_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.telnyx_api_key = "test"
        s.telnyx_timeout = 30
        mock_settings.return_value = s
        adapter = TelnyxAdapter()

    empty_resp = MagicMock(spec=httpx.Response)
    empty_resp.raise_for_status = MagicMock()
    empty_resp.json.return_value = {"data": []}

    found_resp = MagicMock(spec=httpx.Response)
    found_resp.raise_for_status = MagicMock()
    found_resp.json.return_value = {
        "data": [
            {
                "phone_number": "+447911123456",
                "cost_information": {"upfront_cost": "1.00"},
            }
        ]
    }

    order_resp = MagicMock(spec=httpx.Response)
    order_resp.raise_for_status = MagicMock()
    order_resp.json.return_value = {"data": {"id": "order-telnyx-1"}}

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = MagicMock()
        client.get = AsyncMock(side_effect=[empty_resp, found_resp])
        client.post = AsyncMock(return_value=order_resp)
        mock_client_fn.return_value = client

        result = await adapter.purchase_number("whatsapp", "GB", city="Manchester")

    assert result.phone_number == "+447911123456"
    assert result.city_honoured is False
    assert result.city_note is not None
    assert "Manchester" in result.city_note


@pytest.mark.asyncio
async def test_telnyx_empty_country_raises_no_inventory_country():
    """When Telnyx has no inventory for country at all, raises ProviderError(no_inventory_country)."""
    from app.services.providers.telnyx_adapter import TelnyxAdapter
    import httpx

    with patch("app.services.providers.telnyx_adapter.get_settings") as mock_settings:
        s = MagicMock()
        s.telnyx_api_key = "test"
        s.telnyx_timeout = 30
        mock_settings.return_value = s
        adapter = TelnyxAdapter()

    empty_resp = MagicMock(spec=httpx.Response)
    empty_resp.raise_for_status = MagicMock()
    empty_resp.json.return_value = {"data": []}

    with patch.object(adapter, "_get_client") as mock_client_fn:
        client = MagicMock()
        client.get = AsyncMock(return_value=empty_resp)
        mock_client_fn.return_value = client

        with pytest.raises(ProviderError) as exc_info:
            await adapter.purchase_number("whatsapp", "GB")

    assert exc_info.value.category == "no_inventory_country"


# ── provider failover on no_inventory_country ─────────────────────────────────


@pytest.mark.asyncio
async def test_telnyx_empty_country_failover_to_fivesim():
    """When Telnyx has no inventory for country, router fails over to 5sim."""
    router = ProviderRouter()

    mock_telnyx = AsyncMock()
    mock_telnyx.name = "telnyx"
    mock_telnyx.enabled = True
    mock_telnyx.purchase_number = AsyncMock(
        side_effect=ProviderError("no_inventory_country", "No Telnyx numbers for GB")
    )

    mock_fivesim = AsyncMock()
    mock_fivesim.name = "5sim"
    mock_fivesim.enabled = True
    mock_fivesim.purchase_number = AsyncMock(
        return_value=_result("5sim", "+447700900123")
    )

    with patch.object(
        router, "get_provider", return_value=(mock_telnyx, True, None)
    ), patch.object(router, "_get_failover_provider", return_value=mock_fivesim), patch(
        "app.services.providers.provider_router.get_settings"
    ) as mock_settings_fn:
        s = MagicMock()
        s.enable_provider_failover = True
        mock_settings_fn.return_value = s

        result = await router.purchase_with_failover(
            "whatsapp", "GB", city="London", user_tier="pro"
        )

    assert result.phone_number == "+447700900123"
    assert "failover" in result.routing_reason


# ── no provider name in error responses ───────────────────────────────────────


def test_provider_error_user_message_has_no_provider_names():
    """User-facing messages must never contain provider names."""
    provider_names = [
        "telnyx",
        "5sim",
        "textverified",
        "Telnyx",
        "5Sim",
        "TextVerified",
    ]

    for category in ProviderError.USER_MESSAGES:
        msg = ProviderError.USER_MESSAGES[category]
        if msg is None:
            continue
        for name in provider_names:
            assert (
                name.lower() not in msg.lower()
            ), f"Provider name '{name}' found in user message for category '{category}': {msg}"


def test_all_providers_failed_clean_message():
    err = ProviderError("all_providers_failed", "Telnyx failed, 5sim failed")
    assert "telnyx" not in err.user_message.lower()
    assert "5sim" not in err.user_message.lower()
    assert "credits were not charged" in err.user_message.lower()
