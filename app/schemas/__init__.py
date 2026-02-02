"""Schemas package for request/response validation."""

# Authentication schemas
# Common schemas (inline)

from typing import Any, Dict, Optional
from pydantic import BaseModel

# Analytics schemas
from .analytics import (
    AnalyticsResponse,
    BusinessMetrics,
    CompetitiveAnalysis,
    CountryAnalytics,
    DailyUsage,
    PredictiveInsight,
    ServiceUsage,
    TrendData,
)
from .auth import (
    APIKeyCreate,
    APIKeyListResponse,
    APIKeyResponse,
    EmailVerificationRequest,
    GoogleAuthRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

# Payment schemas
from .payment import (
    PaymentInitialize,
    PaymentInitializeResponse,
    PaymentVerify,
    PaymentVerifyResponse,
    RefundRequest,
    RefundResponse,
    SubscriptionPlan,
    SubscriptionRequest,
    SubscriptionResponse,
    TransactionHistoryResponse,
    TransactionResponse,
    WalletBalanceResponse,
    WebhookPayload,
)

# System schemas
from .system import ServiceStatus, ServiceStatusSummary, SupportTicketResponse
from .validators import (
    ValidationMixin,
    create_pagination_response,
    sanitize_input,
    validate_api_key_name,
    validate_area_code,
    validate_carrier_name,
    validate_currency_amount,
    validate_duration_hours,
    validate_pagination_params,
    validate_phone_number,
    validate_referral_code,
    validate_service_name,
    validate_webhook_url,
)

# Verification schemas
from .verification import (
    ExtendRentalRequest,
    MessageResponse,
    NumberRentalRequest,
    NumberRentalResponse,
    RetryVerificationRequest,
    ServicePriceResponse,
    VerificationCreate,
    VerificationHistoryResponse,
    VerificationResponse,
)


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Validation utilities

    __all__ = [
    # Authentication
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyListResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "EmailVerificationRequest",
    "GoogleAuthRequest",
    # Verification
    "VerificationCreate",
    "VerificationResponse",
    "MessageResponse",
    "NumberRentalRequest",
    "NumberRentalResponse",
    "ExtendRentalRequest",
    "RetryVerificationRequest",
    "ServicePriceResponse",
    "VerificationHistoryResponse",
    # Payment
    "PaymentInitialize",
    "PaymentInitializeResponse",
    "PaymentVerify",
    "PaymentVerifyResponse",
    "WebhookPayload",
    "TransactionResponse",
    "TransactionHistoryResponse",
    "RefundRequest",
    "RefundResponse",
    "WalletBalanceResponse",
    "SubscriptionPlan",
    "SubscriptionRequest",
    "SubscriptionResponse",
    # Analytics
    "AnalyticsResponse",
    "ServiceUsage",
    "DailyUsage",
    "CountryAnalytics",
    "TrendData",
    "PredictiveInsight",
    "BusinessMetrics",
    "CompetitiveAnalysis",
    # System
    "SupportTicketResponse",
    "ServiceStatus",
    "ServiceStatusSummary",
    # Common
    "ErrorResponse",
    "SuccessResponse",
    # Validators
    "validate_phone_number",
    "validate_service_name",
    "validate_currency_amount",
    "validate_referral_code",
    "validate_api_key_name",
    "validate_webhook_url",
    "validate_duration_hours",
    "validate_area_code",
    "validate_carrier_name",
    "ValidationMixin",
    "sanitize_input",
    "validate_pagination_params",
    "create_pagination_response",
    ]
