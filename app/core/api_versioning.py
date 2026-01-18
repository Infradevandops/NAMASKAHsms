"""API versioning support."""

from fastapi import Header, HTTPException
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class APIVersionManager:
    """Manages API versions."""

    def __init__(self):
        self.versions = {
            "v1": {"status": "active", "deprecated": False},
            "v2": {"status": "active", "deprecated": False},
        }
        self.current_version = "v2"

    def get_version(self, version_header: Optional[str] = None) -> str:
        """Get API version from header or default."""
        if not version_header:
            return self.current_version

        if version_header not in self.versions:
            raise HTTPException(status_code=400, detail="Invalid API version")

        version_info = self.versions[version_header]
        if version_info["deprecated"]:
            logger.warning(f"Deprecated API version used: {version_header}")

        return version_header

    def deprecate_version(self, version: str):
        """Mark version as deprecated."""
        if version in self.versions:
            self.versions[version]["deprecated"] = True
            logger.info(f"API version deprecated: {version}")

    def get_version_info(self, version: str) -> dict:
        """Get version information."""
        return self.versions.get(version, {})


version_manager = APIVersionManager()


def get_api_version(api_version: Optional[str] = Header(None)) -> str:
    """Dependency for getting API version."""
    return version_manager.get_version(api_version)
