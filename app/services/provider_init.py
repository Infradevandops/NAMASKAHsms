"""Initialize unified provider orchestrator."""
from app.services.provider_orchestrator import ProviderOrchestrator, FailoverStrategy

logger = get_logger(__name__)


def create_provider_orchestrator() -> ProviderOrchestrator:
    """Create and configure provider orchestrator."""
    orchestrator = ProviderOrchestrator(strategy=FailoverStrategy.HEALTH_AWARE)

    # Register TextVerified as primary provider
    textverified = TextVerifiedProvider()
    orchestrator.register_provider(
        "textverified",
        textverified,
        is_primary=True,
        priority=100
    )

    # Register 5SIM as fallback
    fivesim = FiveSimProvider()
    orchestrator.register_provider(
        "5sim",
        fivesim,
        is_primary=False,
        priority=50
    )

    logger.info("Provider orchestrator initialized with TextVerified (primary) and \
    5SIM (fallback)")

    return orchestrator


# Global orchestrator instance
provider_orchestrator = create_provider_orchestrator()
