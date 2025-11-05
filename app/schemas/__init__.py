"""Schemas package for request/response validation."""

# Authentication schemas
from .auth import (
    UserCreate, UserUpdate, UserResponse,
    LoginRequest, TokenResponse,
    APIKeyCreate, APIKeyResponse, APIKeyListResponse,
    PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest, GoogleAuthRequest
)

# Verification schemas
from .verification import (
    VerificationCreate, VerificationResponse, MessageResponse,
    NumberRentalRequest, NumberRentalResponse, ExtendRentalRequest,
    RetryVerificationRequest, ServicePriceResponse, VerificationHistoryResponse
)

# Payment schemas
from .payment import (
    PaymentInitialize, PaymentInitializeResponse,
    PaymentVerify, PaymentVerifyResponse, WebhookPayload,
    TransactionResponse, TransactionHistoryResponse,
    RefundRequest, RefundResponse, WalletBalanceResponse,
    SubscriptionPlan, SubscriptionRequest, SubscriptionResponse
)

# Analytics schemas
from .analytics import (
    AnalyticsResponse, ServiceUsage, DailyUsage, CountryAnalytics,
    TrendData, PredictiveInsight, BusinessMetrics, CompetitiveAnalysis
)

# System schemas
from .system import SupportTicketResponse, ServiceStatus, ServiceStatusSummary

# Common schemas (inline)
from typing import Optional, Dict, Any
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Validation utilities
from .validators import (
    validate_phone_number, validate_service_name, validate_currency_amount,
    validate_referral_code, validate_api_key_name, validate_webhook_url,
    validate_duration_hours, validate_area_code, validate_carrier_name,
    ValidationMixin, sanitize_input, validate_pagination_params,
    create_pagination_response
)

__all__ = [
    # Authentication
    "UserCreate", "UserUpdate", "UserResponse",
    "LoginRequest", "TokenResponse",
    "APIKeyCreate", "APIKeyResponse", "APIKeyListResponse",
    "PasswordResetRequest", "PasswordResetConfirm",
    "EmailVerificationRequest", "GoogleAuthRequest",
    
    # Verification
    "VerificationCreate", "VerificationResponse", "MessageResponse",
    "NumberRentalRequest", "NumberRentalResponse", "ExtendRentalRequest",
    "RetryVerificationRequest", "ServicePriceResponse", "VerificationHistoryResponse",
    
    # Payment
    "PaymentInitialize", "PaymentInitializeResponse",
    "PaymentVerify", "PaymentVerifyResponse", "WebhookPayload",
    "TransactionResponse", "TransactionHistoryResponse",
    "RefundRequest", "RefundResponse", "WalletBalanceResponse",
    "SubscriptionPlan", "SubscriptionRequest", "SubscriptionResponse",
    
    # Analytics
    "AnalyticsResponse", "ServiceUsage", "DailyUsage", "CountryAnalytics",
    "TrendData", "PredictiveInsight", "BusinessMetrics", "CompetitiveAnalysis",
    
    # System
    "SupportTicketResponse", "ServiceStatus", "ServiceStatusSummary",
    
    # Common
    "ErrorResponse", "SuccessResponse",
    
    # Validators
    "validate_phone_number", "validate_service_name", "validate_currency_amount",
    "validate_referral_code", "validate_api_key_name", "validate_webhook_url",
    "validate_duration_hours", "validate_area_code", "validate_carrier_name",
    "ValidationMixin", "sanitize_input", "validate_pagination_params",
    "create_pagination_response"
]