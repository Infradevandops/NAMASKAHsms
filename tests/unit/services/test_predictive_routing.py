from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.services.providers.predictive_scorer import PredictiveRouterScorer
from app.services.providers.provider_router import ProviderRouter


@pytest.mark.asyncio
async def test_predictive_ranking_honors_sentiment():
    """Verifies that the router prioritizes providers with better carrier sentiment."""
    db = MagicMock()
    router = ProviderRouter()

    # Mock scorer to simulate TextVerified having better sentiment than 5sim
    with patch(
        "app.services.providers.predictive_scorer.PredictiveRouterScorer.calculate_provider_score"
    ) as mock_score:

        async def side_effect(service, country, provider_name, **kwargs):
            if provider_name == "textverified":
                return 0.9
            if provider_name == "5sim":
                return 0.4
            return 0.1

        mock_score.side_effect = side_effect

        # Mock adapter enabled status using PropertyMock for read-only properties
        with patch.object(
            type(router._get_textverified()), "enabled", new_callable=PropertyMock
        ) as mock_tv_enabled, patch.object(
            type(router._get_fivesim()), "enabled", new_callable=PropertyMock
        ) as mock_5sim_enabled:

            mock_tv_enabled.return_value = True
            mock_5sim_enabled.return_value = True

            # Test routing for UK WhatsApp (non-US to trigger multi-provider scoring)
            winner, _, _ = await router.get_provider(
                db, "whatsapp", "GB", user_tier="pro"
            )

            assert winner.name == "textverified"


@pytest.mark.asyncio
async def test_unhealthy_provider_deranking():
    """Verifies that providers with low health are automatically deranked."""
    db = MagicMock()
    router = ProviderRouter()

    with patch(
        "app.services.providers.predictive_scorer.PredictiveRouterScorer.calculate_provider_score"
    ) as mock_score:

        async def side_effect(service, country, provider_name, **kwargs):
            # Simulate 5sim being 'Healthy' (0.8) and Telnyx 'Unhealthy' (0.2)
            if provider_name == "5sim":
                return 0.8
            if provider_name == "telnyx":
                return 0.2
            return 0.1

        mock_score.side_effect = side_effect

        # Mock adapter enabled status
        with patch.object(
            type(router._get_fivesim()), "enabled", new_callable=PropertyMock
        ) as mock_5sim_enabled, patch.object(
            type(router._get_telnyx()), "enabled", new_callable=PropertyMock
        ) as mock_telnyx_enabled:

            mock_5sim_enabled.return_value = True
            mock_telnyx_enabled.return_value = True

            winner, _, _ = await router.get_provider(
                db, "whatsapp", "GB", user_tier="pro"
            )

            assert winner.name == "5sim"


@pytest.mark.asyncio
async def test_failover_picks_next_best():
    """Verifies that failover uses the scorer to pick the next highest-ranked provider."""
    db = MagicMock()
    router = ProviderRouter()

    # We'll mock the failed provider as 5sim, and next best should be Telnyx
    with patch(
        "app.services.providers.predictive_scorer.PredictiveRouterScorer.calculate_provider_score"
    ) as mock_score:

        async def side_effect(service, country, provider_name, **kwargs):
            if provider_name == "telnyx":
                return 0.7
            if provider_name == "textverified":
                return 0.3
            return 0.1

        mock_score.side_effect = side_effect

        # Mock adapter enabled status
        with patch.object(
            type(router._get_telnyx()), "enabled", new_callable=PropertyMock
        ) as mock_telnyx_enabled, patch.object(
            type(router._get_textverified()), "enabled", new_callable=PropertyMock
        ) as mock_tv_enabled:

            mock_telnyx_enabled.return_value = True
            mock_tv_enabled.return_value = True

            # Mocking 5sim as the failed adapter
            failed_adapter = MagicMock()
            failed_adapter.name = "5sim"

            next_provider = await router._get_failover_provider(
                db, failed_adapter, "GB", "whatsapp", "pro"
            )

            assert next_provider.name == "telnyx"
