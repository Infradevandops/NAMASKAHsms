"""Services package with dependency injection support."""

from sqlalchemy.orm import Session

from .auth_service import AuthService
from .base import BaseService
from .notification_service import NotificationService
from .payment_service import PaymentService


class ServiceFactory:
    """Factory for creating service instances with dependency injection."""

    def __init__(self, db: Session):
        self.db = db
        self._services = {}

    def get_auth_service(self) -> AuthService:
        """Get or create AuthService instance."""
        if "auth" not in self._services:
            self._services["auth"] = AuthService(self.db)
        return self._services["auth"]

    def get_payment_service(self) -> PaymentService:
        """Get or create PaymentService instance."""
        if "payment" not in self._services:
            self._services["payment"] = PaymentService(self.db)
        return self._services["payment"]

    def get_notification_service(self) -> NotificationService:
        """Get or create NotificationService instance."""
        if "notification" not in self._services:
            self._services["notification"] = NotificationService(self.db)
        return self._services["notification"]

    async def cleanup(self):
        """Cleanup async resources."""

        if "payment" in self._services:
            await self._services["payment"].close()


# Dependency injection helpers
def get_service_factory(db: Session) -> ServiceFactory:
    """Get service factory instance."""
    return ServiceFactory(db)


def get_auth_service(db: Session) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)


def get_payment_service(db: Session) -> PaymentService:
    """Get PaymentService instance."""
    return PaymentService(db)


def get_notification_service(db: Session) -> NotificationService:
    """Get NotificationService instance."""
    return NotificationService(db)


__all__ = [
    "BaseService",
    "AuthService",
    "PaymentService",
    "NotificationService",
    "ServiceFactory",
    "get_service_factory",
    "get_auth_service",
    "get_payment_service",
    "get_notification_service",
]
