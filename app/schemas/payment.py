"""Payment and wallet request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.pydantic_compat import BaseModel, Field, field_validator


class AddCreditsRequest(BaseModel):
    """Schema for adding credits request."""

    amount: float = Field(..., gt=0, description="Amount to add (minimum $5)")

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        if v < 5.0:
            raise ValueError("Minimum amount is $5")
        if v > 10000.0:
            raise ValueError("Maximum amount is $10,000")
        return v


class PaymentInitialize(BaseModel):
        """Schema for payment initialization."""

        amount_usd: float = Field(..., gt=0, description="Amount in USD (minimum $5)")
        payment_method: str = Field(default="paystack", description="Payment method")

        @field_validator("amount_usd", mode="before")
        @classmethod
    def validate_amount(cls, v):
        if v < 5.0:
            raise ValueError("Minimum payment amount is $5 USD")
        if v > 10000.0:
            raise ValueError("Maximum payment amount is $10,000 USD")
        return v

        @field_validator("payment_method", mode="before")
        @classmethod
    def validate_payment_method(cls, v):
        if v not in ["paystack"]:
            raise ValueError("Only paystack payment method is supported")
        return v

        model_config = {
        "json_schema_extra": {
            "example": {"amount_usd": 20.0, "payment_method": "paystack"}
        }
        }


class PaymentInitializeResponse(BaseModel):
        """Schema for payment initialization response."""

        payment_id: str = Field(..., description="Payment ID")
        authorization_url: str = Field(..., description="Payment authorization URL")
        access_code: str = Field(..., description="Payment access code")
        reference: str = Field(..., description="Payment reference")

        model_config = {
        "json_schema_extra": {
            "example": {
                "payment_id": "payment_1642680000000",
                "authorization_url": "https://checkout.paystack.com/abc123",
                "access_code": "abc123def456",
                "reference": "ref_1642680000000",
            }
        }
        }


class PaymentResponse(BaseModel):
        """Schema for payment response."""

        payment_id: str = Field(..., description="Payment ID")
        authorization_url: str = Field(..., description="Payment authorization URL")
        access_code: str = Field(..., description="Payment access code")
        reference: str = Field(..., description="Payment reference")

        model_config = {
        "json_schema_extra": {
            "example": {
                "payment_id": "payment_1642680000000",
                "authorization_url": "https://checkout.paystack.com/abc123",
                "access_code": "abc123def456",
                "reference": "ref_1642680000000",
            }
        }
        }


class PaymentVerification(BaseModel):
        """Schema for payment verification."""

        reference: str = Field(..., description="Payment reference to verify")

        model_config = {
        "json_schema_extra": {"example": {"reference": "ref_1642680000000"}}
        }


class PaymentStatus(BaseModel):
        """Schema for payment status response."""

        status: str = Field(..., description="Payment status")
        amount: float = Field(..., description="Payment amount")
        currency: str = Field(..., description="Payment currency")
        reference: str = Field(..., description="Payment reference")
        paid_at: Optional[datetime] = Field(None, description="Payment completion time")

        model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "amount": 20.0,
                "currency": "USD",
                "reference": "ref_1642680000000",
                "paid_at": "2024-01-20T10:00:00Z",
            }
        }
        }


class WalletBalance(BaseModel):
        """Schema for wallet balance response."""

        balance: float = Field(..., description="Current wallet balance")
        currency: str = Field(default="USD", description="Balance currency")
        last_updated: datetime = Field(..., description="Last balance update time")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "balance": 25.50,
                "currency": "USD",
                "last_updated": "2024-01-20T10:00:00Z",
            }
        },
        }


class TransactionHistory(BaseModel):
        """Schema for transaction history response."""

        id: str = Field(..., description="Transaction ID")
        type: str = Field(..., description="Transaction type")
        amount: float = Field(..., description="Transaction amount")
        description: str = Field(..., description="Transaction description")
        status: str = Field(..., description="Transaction status")
        created_at: datetime = Field(..., description="Transaction creation time")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "txn_1642680000000",
                "type": "credit",
                "amount": 20.0,
                "description": "Wallet top-up via Paystack",
                "status": "completed",
                "created_at": "2024-01-20T10:00:00Z",
            }
        },
        }


class RefundRequest(BaseModel):
        """Schema for refund request."""

        transaction_id: str = Field(..., description="Transaction ID to refund")
        amount: Optional[float] = Field(
        None, description="Partial refund amount (full refund if not specified)"
        )
        reason: str = Field(..., description="Refund reason")

        @field_validator("amount", mode="before")
        @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Refund amount must be positive")
        return v

        model_config = {
        "json_schema_extra": {
            "example": {
                "transaction_id": "transaction_1642680000000",
                "amount": 5.0,
                "reason": "Service not delivered",
            }
        }
        }


class RefundResponse(BaseModel):
        """Schema for refund response."""

        refund_id: str = Field(..., description="Refund ID")
        status: str = Field(..., description="Refund status")
        amount: float = Field(..., description="Refund amount")
        reason: str = Field(..., description="Refund reason")
        processed_at: Optional[datetime] = Field(None, description="Refund processing time")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "refund_id": "refund_1642680000000",
                "status": "pending",
                "amount": 5.0,
                "reason": "Service not delivered",
                "processed_at": None,
            }
        },
        }


class PaymentMethodResponse(BaseModel):
        """Schema for payment method response."""

        methods: List[Dict[str, Any]] = Field(..., description="Available payment methods")

        model_config = {
        "json_schema_extra": {
            "example": {
                "methods": [
                    {
                        "name": "paystack",
                        "display_name": "Paystack",
                        "supported_currencies": ["USD", "NGN"],
                        "min_amount": 5.0,
                        "max_amount": 10000.0,
                    }
                ]
            }
        }
        }


class PaymentVerify(BaseModel):
        """Schema for payment verification request."""

        reference: str = Field(..., description="Payment reference to verify")

        model_config = {
        "json_schema_extra": {"example": {"reference": "ref_1642680000000"}}
        }


class PaymentVerifyResponse(BaseModel):
        """Schema for payment verification response."""

        status: str = Field(..., description="Payment verification status")
        amount_credited: float = Field(..., description="Amount credited to wallet")
        new_balance: float = Field(..., description="New wallet balance after credit")
        reference: str = Field(..., description="Payment reference")
        message: str = Field(..., description="Verification message")

        model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "amount_credited": 20.0,
                "new_balance": 45.50,
                "reference": "ref_1642680000000",
                "message": "Payment verified and credited successfully",
            }
        }
        }


class TransactionResponse(BaseModel):
        """Schema for individual transaction response."""

        id: str = Field(..., description="Transaction ID")
        type: str = Field(..., description="Transaction type")
        amount: float = Field(..., description="Transaction amount")
        description: str = Field(..., description="Transaction description")
        status: str = Field(..., description="Transaction status")
        created_at: datetime = Field(..., description="Transaction creation time")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "txn_1642680000000",
                "type": "credit",
                "amount": 20.0,
                "description": "Wallet top-up via Paystack",
                "status": "completed",
                "created_at": "2024-01-20T10:00:00Z",
            }
        },
        }


class TransactionHistoryResponse(BaseModel):
        """Schema for transaction history response."""

        transactions: List[TransactionResponse] = Field(..., description="List of transactions")
        total_count: int = Field(..., description="Total number of transactions")

        model_config = {
        "json_schema_extra": {
            "example": {
                "transactions": [
                    {
                        "id": "txn_1642680000000",
                        "type": "credit",
                        "amount": 20.0,
                        "description": "Wallet top-up via Paystack",
                        "status": "completed",
                        "created_at": "2024-01-20T10:00:00Z",
                    }
                ],
                "total_count": 1,
            }
        }
        }


class WalletBalanceResponse(BaseModel):
        """Schema for wallet balance response."""

        credits: float = Field(..., description="Current wallet credits")
        credits_usd: float = Field(..., description="Credits in USD")
        free_verifications: int = Field(..., description="Free verifications remaining")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "credits": 25.50,
                "credits_usd": 25.50,
                "free_verifications": 3,
            }
        },
        }


class WebhookPayload(BaseModel):
        """Schema for webhook payload."""

        event: str = Field(..., description="Webhook event type")
        data: Dict[str, Any] = Field(..., description="Webhook data")

        model_config = {
        "json_schema_extra": {
            "example": {
                "event": "charge.success",
                "data": {
                    "id": 123456,
                    "reference": "ref_1642680000000",
                    "amount": 2000,
                    "status": "success",
                },
            }
        }
        }


class SubscriptionPlan(BaseModel):
        """Schema for subscription plan."""

        id: str = Field(..., description="Plan ID")
        name: str = Field(..., description="Plan name")
        price: float = Field(..., description="Plan price")
        currency: str = Field(..., description="Plan currency")
        interval: str = Field(..., description="Billing interval")
        features: List[str] = Field(..., description="Plan features")

        model_config = {
        "json_schema_extra": {
            "example": {
                "id": "plan_basic",
                "name": "Basic Plan",
                "price": 9.99,
                "currency": "USD",
                "interval": "monthly",
                "features": ["100 verifications", "Email support"],
            }
        }
        }


class SubscriptionRequest(BaseModel):
        """Schema for subscription request."""

        plan_id: str = Field(..., description="Plan ID to subscribe to")
        payment_method: str = Field(default="paystack", description="Payment method")

        model_config = {
        "json_schema_extra": {
            "example": {"plan_id": "plan_basic", "payment_method": "paystack"}
        }
        }


class SubscriptionResponse(BaseModel):
        """Schema for subscription response."""

        subscription_id: str = Field(..., description="Subscription ID")
        plan_id: str = Field(..., description="Plan ID")
        status: str = Field(..., description="Subscription status")
        current_period_start: datetime = Field(..., description="Current period start")
        current_period_end: datetime = Field(..., description="Current period end")
        next_billing_date: datetime = Field(..., description="Next billing date")

        model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "subscription_id": "sub_1642680000000",
                "plan_id": "plan_basic",
                "status": "active",
                "current_period_start": "2024-01-20T10:00:00Z",
                "current_period_end": "2024-02-20T10:00:00Z",
                "next_billing_date": "2024-02-20T10:00:00Z",
            }
        },
        }
