"""Number blacklist model."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from app.models.base import BaseModel


class NumberBlacklist(BaseModel):
    """Blacklisted phone numbers."""

    __tablename__ = "number_blacklist"

    user_id = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    country = Column(String)

    # Blacklist reason
    reason = Column(String, default="failed_verification")

    # Auto - blacklist or manual
    is_manual = Column(Boolean, default=False)

    # Expiry (30 days default)
    expires_at = Column(DateTime, nullable=False)

    @property
    def is_expired(self) -> bool:
        """Check if blacklist entry is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @classmethod
    def create_blacklist_entry(
        cls,
        user_id: str,
        phone_number: str,
        service_name: str,
        country: str = None,
        reason: str = "failed_verification",
        is_manual: bool = False,
        days: int = 30,
    ):
        """Create a new blacklist entry."""
        return cls(
            user_id=user_id,
            phone_number=phone_number,
            service_name=service_name,
            country=country,
            reason=reason,
            is_manual=is_manual,
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
        )
