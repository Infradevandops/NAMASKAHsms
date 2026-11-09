"""EmailOutbox — durable email intent table with lease-based worker processing."""

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.models.base import BaseModel


class EmailOutbox(BaseModel):
    """
    Persists email intent atomically with the business event that triggered it.

    Status lifecycle:
        pending → processing → provider_accepted → delivered
                             → retry_wait → (back to pending)
                             → suppressed
                             → failed_permanent
    """

    __tablename__ = "email_outbox"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_email_outbox_idempotency_key"),
    )

    # Stable key derived from the business event (e.g. "payment-receipt:paystack:REF123")
    idempotency_key = Column(String(255), nullable=False, index=True)

    # Classification
    email_class = Column(String(50), nullable=False)   # EmailClass value
    category = Column(String(50), nullable=True)        # notification category
    template_key = Column(String(100), nullable=True)

    # Recipient — store only what is needed; never log full payload
    recipient_email = Column(String(255), nullable=False)

    # Serialised template payload (JSON string)
    payload_json = Column(Text, nullable=True)

    # Status
    status = Column(String(30), nullable=False, default="pending", index=True)

    # Retry tracking
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_attempt_at = Column(DateTime, nullable=True, index=True)

    # Lease (worker claims a row by setting lease_owner + lease_expires_at)
    lease_owner = Column(String(100), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)

    # Provider result
    provider_name = Column(String(50), nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    last_error = Column(String(500), nullable=True)

    # Timestamps
    accepted_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    terminal_at = Column(DateTime, nullable=True)

    # Correlation
    source_event_id = Column(String(255), nullable=True, index=True)
