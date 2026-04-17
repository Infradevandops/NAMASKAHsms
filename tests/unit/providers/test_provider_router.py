"""Unit tests for provider router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.providers.base_provider import PurchaseResult
from app.services.providers.provider_errors import ProviderError
from app.services.providers.provider_router import ProviderRouter


class TestProviderRouter:
    """Test suite for ProviderRouter."""

    @pytest.fixture
    def router(self):
        """Create router instance."""
        return ProviderRouter()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("app.services.providers.provider_router.get_settings") as mock:
            settings = MagicMock()
            settings.enable_provider_failover = True
            settings.prefer_enterprise_provider = False
            mock.return_value = settings
            yield settings

    @pytest.mark.asyncio
    async def test_us_routes_to_textverified(self, router):
        """US requests should route to TextVerified."""
        provider, _, _ = await router.get_provider("whatsapp", "US")
        assert provider.name == "textverified"

    @pytest.mark.asyncio
    async def test_international_routes_to_fivesim(self, router):
        """International requests should route to 5sim if no specialist is available."""
        with patch.object(router, "_get_fivesim") as mock_fivesim, \
             patch.object(router, "_pvapins_covers", return_value=False), \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
            mock_provider = MagicMock()
            mock_provider.enabled = True
            mock_provider.name = "5sim"
            mock_fivesim.return_value = mock_provider

            provider, _, _ = await router.get_provider("whatsapp", "GB")
            assert provider.name == "5sim"

    @pytest.mark.asyncio
    async def test_enterprise_preference_routes_to_telnyx(self, router):
        """Enterprise preference should route to Telnyx."""
        with patch.object(router, "_get_telnyx") as mock_telnyx, \
             patch.object(router, "_pvapins_covers", return_value=False), \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
            mock_provider = MagicMock()
            mock_provider.enabled = True
            mock_provider.name = "telnyx"
            mock_telnyx.return_value = mock_provider

            provider, _, _ = await router.get_provider("whatsapp", "GB", prefer_enterprise=True)
            assert provider.name == "telnyx"

    @pytest.mark.asyncio
    async def test_fallback_to_textverified_when_no_international_provider(self, router):
        """Should fallback to TextVerified when no international provider available."""
        with patch.object(router, "_get_fivesim") as mock_fivesim, \
             patch.object(router, "_get_telnyx") as mock_telnyx, \
             patch.object(router, "_get_pvapins") as mock_pvapins, \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
 
            mock_fivesim_provider = MagicMock()
            mock_fivesim_provider.enabled = False
            mock_fivesim.return_value = mock_fivesim_provider
 
            mock_telnyx_provider = MagicMock()
            mock_telnyx_provider.enabled = False
            mock_telnyx.return_value = mock_telnyx_provider
 
            mock_pvapins_provider = MagicMock()
            mock_pvapins_provider.enabled = False
            mock_pvapins.return_value = mock_pvapins_provider
 
            provider, _, _ = await router.get_provider("whatsapp", "GB")
            assert provider.name == "textverified"

    @pytest.mark.asyncio
    async def test_purchase_with_failover_success(self, router, mock_settings):
        """Successful purchase should return result."""
        mock_provider = AsyncMock()
        mock_provider.name = "textverified"
        mock_result = PurchaseResult(
            phone_number="+12025551234",
            order_id="test123",
            cost=2.22,
            expires_at="2026-03-26T12:00:00Z",
            provider="textverified",
        )
        mock_provider.purchase_number.return_value = mock_result

        with patch.object(router, "get_provider", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (mock_provider, False, None)
            result = await router.purchase_with_failover(
                service="whatsapp",
                country="US",
            )
 
            assert result.phone_number == "+12025551234"
            assert result.provider == "textverified"
            mock_provider.purchase_number.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_failover_on_insufficient_balance(self, router, mock_settings):
        """Should NOT failover on insufficient balance error — propagates as RuntimeError."""
        mock_provider = AsyncMock()
        mock_provider.name = "textverified"
        mock_provider.purchase_number.side_effect = RuntimeError("Insufficient balance")

        with patch.object(router, "get_provider", return_value=(mock_provider, False, None)):
            with pytest.raises(RuntimeError, match="Insufficient balance"):
                await router.purchase_with_failover(
                    service="whatsapp",
                    country="US",
                )

    @pytest.mark.asyncio
    async def test_no_failover_on_no_inventory(self, router, mock_settings):
        """Should NOT failover on no inventory error — propagates as RuntimeError."""
        mock_provider = AsyncMock()
        mock_provider.name = "textverified"
        mock_provider.purchase_number.side_effect = RuntimeError(
            "No inventory available"
        )

        with patch.object(router, "get_provider", return_value=(mock_provider, False, None)):
            with pytest.raises(RuntimeError, match="No inventory"):
                await router.purchase_with_failover(
                    service="whatsapp",
                    country="US",
                )

    @pytest.mark.asyncio
    async def test_failover_on_network_error(self, router, mock_settings):
        """Should failover on network/infrastructure error."""
        mock_primary = AsyncMock()
        mock_primary.name = "textverified"
        mock_primary.purchase_number.side_effect = ProviderError(
            "provider_unreachable", "Connection timeout"
        )

        mock_secondary = AsyncMock()
        mock_secondary.name = "telnyx"
        mock_result = PurchaseResult(
            phone_number="+442071234567",
            order_id="telnyx123",
            cost=0.50,
            expires_at="2026-03-26T12:00:00Z",
            provider="telnyx",
        )
        mock_secondary.purchase_number.return_value = mock_result

        with patch.object(
            router, "get_provider", new_callable=AsyncMock
        ) as mock_get, patch.object(
            router, "_get_failover_provider", new_callable=AsyncMock
        ) as mock_failover:
            mock_get.return_value = (mock_primary, False, None)
            mock_failover.return_value = mock_secondary

            result = await router.purchase_with_failover(
                service="whatsapp",
                country="GB",
            )

            assert result.phone_number == "+442071234567"
            assert result.provider == "telnyx"
            assert "failover" in result.routing_reason

    @pytest.mark.asyncio
    async def test_failover_disabled(self, router):
        """Should NOT failover when disabled — RuntimeError propagates."""
        with patch(
            "app.services.providers.provider_router.get_settings"
        ) as mock_settings_func:
            settings = MagicMock()
            settings.enable_provider_failover = False
            mock_settings_func.return_value = settings

            mock_provider = AsyncMock()
            mock_provider.name = "textverified"
            mock_provider.purchase_number.side_effect = RuntimeError(
                "Connection timeout"
            )

            with patch.object(router, "get_provider", return_value=(mock_provider, False, None)):
                with pytest.raises(RuntimeError, match="Connection timeout"):
                    await router.purchase_with_failover(
                        service="whatsapp",
                        country="US",
                    )

    @pytest.mark.asyncio
    async def test_get_provider_balances(self, router):
        """Should return balances from all enabled providers."""
        mock_tv = AsyncMock()
        mock_tv.enabled = True
        mock_tv.get_balance.return_value = 100.0

        mock_telnyx = AsyncMock()
        mock_telnyx.enabled = True
        mock_telnyx.get_balance.return_value = 50.0

        mock_fivesim = AsyncMock()
        mock_fivesim.enabled = False

        mock_pvapins = AsyncMock()
        mock_pvapins.enabled = True
        mock_pvapins.get_balance.return_value = 25.0

        with patch.object(router, "_get_textverified", return_value=mock_tv), \
             patch.object(router, "_get_telnyx", return_value=mock_telnyx), \
             patch.object(router, "_get_fivesim", return_value=mock_fivesim), \
             patch.object(router, "_get_pvapins", return_value=mock_pvapins):

            balances = await router.get_provider_balances()

            assert balances["textverified"] == 100.0
            assert balances["telnyx"] == 50.0
            assert balances["pvapins"] == 25.0
            assert "5sim" not in balances

    def test_get_enabled_providers(self, router):
        """Should return list of enabled provider names."""
        mock_tv = MagicMock()
        mock_tv.enabled = True

        mock_telnyx = MagicMock()
        mock_telnyx.enabled = True

        mock_fivesim = MagicMock()
        mock_fivesim.enabled = False

        mock_pvapins = MagicMock()
        mock_pvapins.enabled = True

        with patch.object(router, "_get_textverified", return_value=mock_tv), \
             patch.object(router, "_get_telnyx", return_value=mock_telnyx), \
             patch.object(router, "_get_fivesim", return_value=mock_fivesim), \
             patch.object(router, "_get_pvapins", return_value=mock_pvapins):

            enabled = router.get_enabled_providers()

            assert "textverified" in enabled
            assert "telnyx" in enabled
            assert "pvapins" in enabled
            assert "5sim" not in enabled

    @pytest.mark.asyncio
    async def test_failover_provider_selection_textverified_failed(self, router):
        """When TextVerified fails, should try Telnyx then 5sim."""
        mock_tv = MagicMock()
        mock_tv.name = "textverified"
 
        mock_telnyx = MagicMock()
        mock_telnyx.enabled = True
 
        with patch.object(router, "_get_telnyx", return_value=mock_telnyx), \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
            failover = await router._get_failover_provider(mock_tv, "GB", "whatsapp")
            assert failover == mock_telnyx

    @pytest.mark.asyncio
    async def test_failover_provider_selection_telnyx_failed(self, router):
        """When Telnyx fails, should try 5sim then TextVerified."""
        mock_telnyx = MagicMock()
        mock_telnyx.name = "telnyx"
 
        mock_fivesim = MagicMock()
        mock_fivesim.enabled = True
 
        with patch.object(router, "_get_fivesim", return_value=mock_fivesim), \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
            failover = await router._get_failover_provider(mock_telnyx, "GB", "whatsapp")
            assert failover == mock_fivesim

    @pytest.mark.asyncio
    async def test_failover_provider_selection_fivesim_failed(self, router):
        """When 5sim fails, should try PVApins then Telnyx then TextVerified."""
        mock_fivesim = MagicMock()
        mock_fivesim.name = "5sim"
 
        mock_pvapins = MagicMock()
        mock_pvapins.enabled = True
 
        with patch.object(router, "_get_pvapins", return_value=mock_pvapins), \
             patch.object(router, "_pvapins_covers", return_value=True), \
             patch("app.services.purchase_intelligence.PurchaseIntelligenceService.get_live_health_score", return_value=1.0):
            failover = await router._get_failover_provider(mock_fivesim, "GB", "whatsapp")
            assert failover == mock_pvapins
