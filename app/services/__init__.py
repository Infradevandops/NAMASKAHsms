"""Services package with dependency injection support."""

from sqlalchemy.orm import Session
from .base import BaseService
from .auth_service import AuthService
# Temporarily disabled due to syntax errors
# from .payment_service import PaymentService


class ServiceFactory:
    """Factory for creating service instances with dependency injection."""

    def __init__(self, db: Session):
        self.db = db
        self._services = {}

    def get_auth_service(self):
        """Get or create AuthService instance."""
        if "auth" not in self._services:
            self._services["auth"] = AuthService(self.db)
        return self._services["auth"]


# Dependency injection helpers
def get_service_factory(db: Session) -> ServiceFactory:
    """Get service factory instance."""
    return ServiceFactory(db)


def get_auth_service(db: Session):
    """Get AuthService instance."""
    return AuthService(db)


__all__ = [
    "BaseService",
    "ServiceFactory", 
    "get_service_factory",
    "get_auth_service",
]