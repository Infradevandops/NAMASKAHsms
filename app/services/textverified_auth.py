"""TextVerified Authentication - SDK handles this."""
from app.core.config import settings

logger = get_logger(__name__)


class TextVerifiedAuthService:
    """Auth wrapper - SDK handles authentication internally."""

    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.api_username = getattr(settings, "textverified_email", "")

    async def get_headers(self) -> dict:
        """SDK handles headers internally."""
        return {}


def get_textverified_auth() -> TextVerifiedAuthService:
    """Get auth service instance."""
    return TextVerifiedAuthService()
