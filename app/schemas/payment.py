"""Payment and wallet request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PaymentInitialize(BaseModel):
    """Schema for payment initialization."""

    amount_usd: float = Field(..., gt=0, description="Amount in USD (minimum $5)")
    payment_method: str = Field(default="paystack", description="Payment method")

    @validator("amount_usd")
    def validate_amount(cls, v):
        if v < 5.0:
            raise ValueError("Minimum payment amount is $5 USD")
        if v > 10000.0:
            raise ValueError("Maximum payment amount is $10,000 USD")
        return v

    @validator("payment_method")
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

    success: bool
    authorization_url: str = Field(..., description="Paystack checkout URL")
    access_code: str = Field(..., description="Paystack access code")
    reference: str = Field(..., description="Payment reference")
    payment_details: Dict[str, Any] = Field(..., description="Payment breakdown")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "authorization_url": "https://checkout.paystack.com/abc123",
                "access_code": "access_code_123",
                "reference": "namaskah_user123_1642680000",
                "payment_details": {
                    "namaskah_amount": 10.0,
                    "usd_amount": 20.0,
                    "ngn_amount": 29600.0,
                    "exchange_rate": 1480.0,
                },
            }
        }
    }


class PaymentVerify(BaseModel):
    """Schema for payment verification."""

    reference: str = Field(..., description="Payment reference to verify")

    model_config = {
        "json_schema_extra": {"example": {"reference": "namaskah_user123_1642680000"}}
    }


class PaymentVerifyResponse(BaseModel):
    """Schema for payment verification response."""

    status: str = Field(..., description="Payment status")
    amount_credited: float = Field(..., description="Amount credited to wallet")
    new_balance: float = Field(..., description="New wallet balance")
    reference: str = Field(..., description="Payment reference")
    message: str = Field(..., description="Status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "amount_credited": 10.0,
                "new_balance": 25.5,
                "reference": "namaskah_user123_1642680000",
                "message": "Payment verified and credited successfully",
            }
        }
    }


class WebhookPayload(BaseModel):
    """Schema for Paystack webhook payload."""

    event: str = Field(..., description="Webhook event type")
    data: Dict[str, Any] = Field(..., description="Webhook data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event": "charge.success",
                "data": {
                    "reference": "namaskah_user123_1642680000",
                    "amount": 2960000,
                    "status": "success",
                    "metadata": {"user_id": "user_123", "namaskah_amount": 10.0},
                },
            }
        }
    }


class TransactionResponse(BaseModel):
    """Schema for transaction response."""

    id: str
    amount: float
    type: str = Field(..., description="Transaction type: credit or debit")
    description: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "transaction_1642680000000",
                "amount": 10.0,
                "type": "credit",
                "description": "Paystack payment: ref_123",
                "created_at": "2024-01-20T10:00:00Z",
            }
        },
    }


class TransactionHistoryResponse(BaseModel):
    """Schema for transaction history."""

    transactions: List[TransactionResponse]
    total_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "transactions": [
                    {
                        "id": "transaction_1642680000000",
                        "amount": 10.0,
                        "type": "credit",
                        "description": "Paystack payment: ref_123",
                        "created_at": "2024-01-20T10:00:00Z",
                    }
                ],
                "total_count": 1,
            }
        }
    }


class RefundRequest(BaseModel):
    """Schema for refund request."""

    transaction_id: str = Field(..., description="Transaction ID to refund")
    amount: Optional[float] = Field(
        None, gt=0, description="Partial refund amount (optional)"
    )
    reason: str = Field(..., description="Refund reason")

    @validator("amount")
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

    success: bool
    refund_id: str
    amount_refunded: float
    status: str
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "refund_id": "refund_123",
                "amount_refunded": 5.0,
                "status": "processing",
                "message": "Refund initiated successfully",
            }
        }
    }


class WalletBalanceResponse(BaseModel):
    """Schema for wallet balance response."""

    credits: float = Field(..., description="Current Namaskah credits")
    credits_usd: float = Field(..., description="Credits value in USD")
    free_verifications: float = Field(..., description="Free verifications remaining")

    model_config = {
        "json_schema_extra": {
            "example": {"credits": 15.5, "credits_usd": 31.0, "free_verifications": 1.0}
        }
    }


class SubscriptionPlan(BaseModel):
    """Schema for subscription plan."""

    id: str
    name: str
    price: float = Field(..., description="Monthly price in Namaskah credits")
    price_usd: float = Field(..., description="Monthly price in USD")
    discount: str = Field(..., description="Discount percentage")
    free_verifications: int = Field(..., description="Free verifications per month")
    features: List[str] = Field(..., description="Plan features")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "pro",
                "name": "Pro Plan",
                "price": 12.5,
                "price_usd": 25.0,
                "discount": "20%",
                "free_verifications": 5,
                "features": [
                    "20% discount on all verifications",
                    "5 free verifications per month",
                    "Priority support",
                ],
            }
        }
    }


class SubscriptionRequest(BaseModel):
    """Schema for subscription request."""

    plan_id: str = Field(..., description="Plan ID to subscribe to")

    @validator("plan_id")
    def validate_plan_id(cls, v):
        if v not in ["pro", "turbo"]:
            raise ValueError("Plan ID must be pro or turbo")
        return v

    model_config = {"json_schema_extra": {"example": {"plan_id": "pro"}}}


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""

    plan: str
    name: str
    status: str
    price: float
    discount: str
    expires_at: Optional[str]
    features: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "plan": "pro",
                "name": "Pro Plan",
                "status": "active",
                "price": 12.5,
                "discount": "20%",
                "expires_at": "2024-02-20T10:00:00Z",
                "features": {"discount": 0.20, "free_verifications": 5},
            }
        }
    }
