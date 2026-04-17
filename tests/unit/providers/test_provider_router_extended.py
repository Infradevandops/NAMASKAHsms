"""Additional provider router tests — Issue 6 from STABILITY_CHECKLIST.md."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.base_provider import PurchaseResult
from app.services.providers.provider_router import ProviderRouter


@pytest.fixture
def router():
    return ProviderRouter()


def _make_result(provider="textverified"):
    return PurchaseResult(
        phone_number="+12025551234",
        order_id="order-1",
        cost=2.22,
        expires_at="2026-03-26T12:00:00Z",
        provider=provider,
    )


# ── balance edge cases ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_provider_balances_all_fail(router):
    mock_tv = AsyncMock()
    mock_tv.enabled = True
    mock_tv.get_balance = AsyncMock(side_effect=Exception("API error"))

    mock_telnyx = AsyncMock()
    mock_telnyx.enabled = True
    mock_telnyx.get_balance = AsyncMock(side_effect=Exception("API error"))

    mock_fivesim = AsyncMock()
    mock_fivesim.enabled = True
    mock_fivesim.get_balance = AsyncMock(side_effect=Exception("API error"))

    with patch.object(router, "_get_textverified", return_value=mock_tv), patch.object(
        router, "_get_telnyx", return_value=mock_telnyx
    ), patch.object(router, "_get_fivesim", return_value=mock_fivesim):

        balances = await router.get_provider_balances()

    assert balances["textverified"] == 0.0
    assert balances["telnyx"] == 0.0
    assert balances["5sim"] == 0.0


@pytest.mark.asyncio
async def test_get_provider_balances_partial_fail(router):
    mock_tv = AsyncMock()
    mock_tv.enabled = True
    mock_tv.get_balance = AsyncMock(return_value=100.0)

    mock_telnyx = AsyncMock()
    mock_telnyx.enabled = True
    mock_telnyx.get_balance = AsyncMock(side_effect=Exception("API error"))

    mock_fivesim = AsyncMock()
    mock_fivesim.enabled = False

    with patch.object(router, "_get_textverified", return_value=mock_tv), patch.object(
        router, "_get_telnyx", return_value=mock_telnyx
    ), patch.object(router, "_get_fivesim", return_value=mock_fivesim):

        balances = await router.get_provider_balances()

    assert balances["textverified"] == 100.0
    assert balances["telnyx"] == 0.0
    assert "5sim" not in balances


# ── all providers fail ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_purchase_all_providers_fail(router):
    mock_primary = AsyncMock()
    mock_primary.name = "textverified"
    mock_primary.purchase_number = AsyncMock(
        side_effect=RuntimeError("Connection timeout")
    )

    mock_secondary = AsyncMock()
    mock_secondary.name = "telnyx"
    mock_secondary.purchase_number = AsyncMock(
        side_effect=RuntimeError("Connection timeout")
    )

    with patch(
        "app.services.providers.provider_router.get_settings"
    ) as mock_settings_fn:
        s = MagicMock()
        s.enable_provider_failover = True
        mock_settings_fn.return_value = s

        with patch.object(
            router, "get_provider", return_value=(mock_primary, False, None)
        ), patch.object(router, "_get_failover_provider", return_value=mock_secondary):

            with pytest.raises(RuntimeError, match="All providers failed"):
                await router.purchase_with_failover("whatsapp", "US")


# ── concurrent failover ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_purchase_concurrent_failover(router):
    """10 concurrent requests all failover correctly."""
    import asyncio

    mock_primary = AsyncMock()
    mock_primary.name = "textverified"
    mock_primary.purchase_number = AsyncMock(
        side_effect=RuntimeError("Connection timeout")
    )

    mock_secondary = AsyncMock()
    mock_secondary.name = "telnyx"
    mock_secondary.purchase_number = AsyncMock(return_value=_make_result("telnyx"))

    with patch(
        "app.services.providers.provider_router.get_settings"
    ) as mock_settings_fn:
        s = MagicMock()
        s.enable_provider_failover = True
        mock_settings_fn.return_value = s

        with patch.object(
            router, "get_provider", return_value=(mock_primary, False, None)
        ), patch.object(router, "_get_failover_provider", return_value=mock_secondary):

            tasks = [router.purchase_with_failover("whatsapp", "US") for _ in range(10)]
            results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all(r.provider == "telnyx" for r in results)


# ── enabled providers ─────────────────────────────────────────────────────────


def test_get_enabled_providers_none_enabled(router):
    mock_tv = MagicMock()
    mock_tv.enabled = False
    mock_telnyx = MagicMock()
    mock_telnyx.enabled = False
    mock_fivesim = MagicMock()
    mock_fivesim.enabled = False

    with patch.object(router, "_get_textverified", return_value=mock_tv), patch.object(
        router, "_get_telnyx", return_value=mock_telnyx
    ), patch.object(router, "_get_fivesim", return_value=mock_fivesim):

        enabled = router.get_enabled_providers()

    assert enabled == []


# ── routing_reason populated ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_routing_reason_populated(router):
    mock_provider = AsyncMock()
    mock_provider.name = "textverified"
    mock_provider.purchase_number = AsyncMock(return_value=_make_result())

    with patch.object(router, "get_provider", return_value=(mock_provider, False, None)):
        result = await router.purchase_with_failover("whatsapp", "US")

    assert result.routing_reason == "country=US"


@pytest.mark.asyncio
async def test_routing_reason_failover_populated(router):
    mock_primary = AsyncMock()
    mock_primary.name = "textverified"
    mock_primary.purchase_number = AsyncMock(
        side_effect=RuntimeError("Connection timeout")
    )

    mock_secondary = AsyncMock()
    mock_secondary.name = "telnyx"
    mock_secondary.purchase_number = AsyncMock(return_value=_make_result("telnyx"))

    with patch(
        "app.services.providers.provider_router.get_settings"
    ) as mock_settings_fn:
        s = MagicMock()
        s.enable_provider_failover = True
        mock_settings_fn.return_value = s

        with patch.object(
            router, "get_provider", return_value=(mock_primary, False, None)
        ), patch.object(router, "_get_failover_provider", return_value=mock_secondary):

            result = await router.purchase_with_failover("whatsapp", "US")

    assert "failover" in result.routing_reason


# ── failover circular guard ───────────────────────────────────────────────────


def test_failover_no_circular_loop(router):
    """_get_failover_provider never returns the same provider that failed."""
    mock_tv = MagicMock()
    mock_tv.name = "textverified"
    mock_tv.enabled = True

    # If textverified failed, failover should NOT return textverified
    with patch.object(router, "_get_telnyx") as mock_telnyx_fn, patch.object(
        router, "_get_fivesim"
    ) as mock_fivesim_fn:

        mock_telnyx = MagicMock()
        mock_telnyx.enabled = False
        mock_telnyx_fn.return_value = mock_telnyx

        mock_fivesim = MagicMock()
        mock_fivesim.enabled = False
        mock_fivesim_fn.return_value = mock_fivesim

        result = router._get_failover_provider(mock_tv, "US")

    # No enabled secondary → returns None, not the same provider
    assert result is None
