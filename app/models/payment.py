"""Payment - related database models."""
from sqlalchemy import Boolean, Column, Float, String, Text

from app.models.base import BaseModel


class PaymentLog(BaseModel):
    """Payment transaction logging."""

    __tablename__ = "payment_logs"

    user_id = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False)
    reference = Column(String, unique=True, nullable=False, index=True)
    amount_ngn = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=False)
    namaskah_amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="initialized", index=True)
    payment_method = Column(String, nullable=False, default="paystack")
    webhook_received = Column(Boolean, default=False)
    credited = Column(Boolean, default=False)
    error_message = Column(Text)
