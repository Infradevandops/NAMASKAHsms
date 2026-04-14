"""Provider error types with clean user-facing messages.

Internal error details (provider names, API responses) stay in logs.
User-facing messages are generic, professional, and provider-agnostic.
"""


class ProviderError(Exception):
    """Structured error from any SMS provider.

    category  -- machine-readable error type (used for routing decisions)
    internal  -- full detail for logs only, NEVER shown to users
    """

    # Clean user-facing messages — no provider names, no technical detail
    USER_MESSAGES = {
        "timeout": "Verification is taking longer than expected. Please try again.",
        "no_inventory_city": None,  # Not an error — handled as city_honoured=False
        "no_inventory_country": "No numbers available for this country right now. Please try again later.",
        "unsupported_country": "This country is not currently supported.",
        "unsupported_service": "This service is not currently supported.",
        "provider_unreachable": "Verification service is temporarily unavailable. Please try again.",
        "all_providers_failed": "Verification is temporarily unavailable. Your credits were not charged.",
        "not_configured": "Verification service is temporarily unavailable. Please try again.",
        "malformed_response": "Verification service is temporarily unavailable. Please try again.",
    }

    def __init__(self, category: str, internal: str = ""):
        self.category = category
        self.internal = internal
        super().__init__(internal or category)

    @property
    def user_message(self) -> str:
        return self.USER_MESSAGES.get(
            self.category,
            "Verification service is temporarily unavailable. Please try again.",
        )

    @property
    def is_reroutable(self) -> bool:
        """True if this error should trigger provider failover."""
        return self.category in (
            "no_inventory_country",
            "provider_unreachable",
            "timeout",
            "not_configured",
        )

    @property
    def is_city_fallback(self) -> bool:
        """True if this error should trigger city-level retry (drop city, same provider)."""
        return self.category == "no_inventory_city"

    @property
    def is_terminal(self) -> bool:
        """True if this error should surface to user immediately without rerouting."""
        return self.category in ("unsupported_country", "unsupported_service")
