"""Transaction and payment - related database models."""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String

from app.models.base import BaseModel


class Transaction(BaseModel):
    """Financial transaction model."""

    __tablename__ = "sms_transactions"

    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False, index=True)  # credit, debit, sms_purchase, etc.
    description = Column(String)
    tier = Column(String)
    service = Column(String)
    filters = Column(String)
    status = Column(String, default="completed")
    
    # Idempotency and linking
    reference = Column(String, unique=True, index=True)
    idempotency_key = Column(String, unique=True, index=True)
    payment_log_id = Column(String, index=True)


class PaymentLog(BaseModel):
    """Payment processing log."""

    __tablename__ = "payment_logs"

    user_id = Column(String, index=True)
    email = Column(String)
    reference = Column(String, unique=True, index=True)
    amount_ngn = Column(Float)
    amount_usd = Column(Float)
    namaskah_amount = Column(Float)
    status = Column(String, index=True)
    payment_method = Column(String)
    webhook_received = Column(Boolean, default=False, nullable=False)
    credited = Column(Boolean, default=False, nullable=False)
    error_message = Column(String)
    
    # Idempotency and state machine
    idempotency_key = Column(String, unique=True, index=True)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    state = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed, refunded
    state_transitions = Column(JSON)  # Audit trail
    lock_version = Column(Integer, default=0, nullable=False)  # Optimistic locking