"""Reseller program models."""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ResellerAccount(BaseModel):

    __tablename__ = "reseller_accounts"

    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    tier = Column(String(50), default="bronze")
    volume_discount = Column(Float, default=0.0)
    custom_rates = Column(JSON, default=lambda: {})
    credit_limit = Column(Float, default=0.0)
    auto_topup_enabled = Column(Boolean, default=False)
    auto_topup_threshold = Column(Float, default=100.0)
    auto_topup_amount = Column(Float, default=500.0)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="reseller_account")
    sub_accounts = relationship("SubAccount", back_populates="reseller")


class SubAccount(BaseModel):

    __tablename__ = "sub_accounts"

    reseller_id = Column(UUID(as_uuid=False), ForeignKey("reseller_accounts.id"), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    credits = Column(Float, default=0.0)
    usage_limit = Column(Float, nullable=True)
    rate_multiplier = Column(Float, default=1.0)
    features = Column(JSON, default=lambda: {})
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, nullable=True)

    # Relationships
    reseller = relationship("ResellerAccount", back_populates="sub_accounts")
    transactions = relationship("SubAccountTransaction", back_populates="sub_account")


class SubAccountTransaction(BaseModel):

    __tablename__ = "sub_account_transactions"

    sub_account_id = Column(UUID(as_uuid=False), ForeignKey("sub_accounts.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # credit, debit, verification
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    reference = Column(String(100), nullable=True)
    balance_after = Column(Float, nullable=False)

    # Relationships
    sub_account = relationship("SubAccount", back_populates="transactions")


class CreditAllocation(BaseModel):

    __tablename__ = "credit_allocations"

    reseller_id = Column(UUID(as_uuid=False), ForeignKey("reseller_accounts.id"), nullable=False)
    sub_account_id = Column(UUID(as_uuid=False), ForeignKey("sub_accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    allocation_type = Column(String(50), default="manual")  # manual, auto_topup, bulk
    notes = Column(String(255), nullable=True)

    # Relationships
    reseller = relationship("ResellerAccount")
    sub_account = relationship("SubAccount")


class BulkOperation(BaseModel):

    __tablename__ = "bulk_operations"

    reseller_id = Column(UUID(as_uuid=False), ForeignKey("reseller_accounts.id"), nullable=False)
    operation_type = Column(String(50), nullable=False)  # credit_topup, account_create, config_update
    total_accounts = Column(Integer, nullable=False)
    processed_accounts = Column(Integer, default=0)
    failed_accounts = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    operation_data = Column(JSON, default=lambda: {})
    error_log = Column(JSON, default=lambda: {})

    # Relationships
    reseller = relationship("ResellerAccount")