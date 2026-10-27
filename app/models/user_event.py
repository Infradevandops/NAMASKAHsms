"""User event tracking model for analytics and monitoring."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Index, String, Text, event
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB
from sqlalchemy.dialects.postgresql import UUID

JSONB = JSON().with_variant(PostgresJSONB, "postgresql")

from app.models.base import Base


class UserEvent(Base):
    """Track user interactions for analytics and behavior analysis."""

    __tablename__ = "user_events"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=lambda: __import__("uuid").uuid4()
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True, default={})
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("idx_user_event_type", "user_id", "event_type"),
        Index("idx_event_created", "event_type", "created_at"),
    )

    # Event type constants
    SIGNUP = "signup"
    LOGIN = "login"
    LOGOUT = "logout"
    FIRST_VERIFICATION = "first_verification"
    VERIFICATION_SUCCESS = "verification_success"
    VERIFICATION_FAILED = "verification_failed"
    TIER_UPGRADE = "tier_upgrade"
    TIER_DOWNGRADE = "tier_downgrade"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    REFUND_ISSUED = "refund_issued"
    FEATURE_USED = "feature_used"
    API_KEY_GENERATED = "api_key_generated"
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    ACCOUNT_SUSPENDED = "account_suspended"
    ACCOUNT_ACTIVATED = "account_activated"
    ACCOUNT_DELETED = "account_deleted"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_VERIFIED = "email_verified"
    PROFILE_UPDATED = "profile_updated"
    SETTINGS_CHANGED = "settings_changed"
    RENTAL_CREATED = "rental_created"
    RENTAL_EXPIRED = "rental_expired"
    VOICE_VERIFICATION_STARTED = "voice_verification_started"
    VOICE_VERIFICATION_COMPLETED = "voice_verification_completed"
    WEBHOOK_CONFIGURED = "webhook_configured"
    AFFILIATE_JOINED = "affiliate_joined"
    COMMISSION_EARNED = "commission_earned"

    def __repr__(self):
        return f"<UserEvent {self.event_type} for user {self.user_id}>"

    @classmethod
    def create(
        cls,
        user_id: str,
        event_type: str,
        event_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Create a new user event."""
        return cls(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
