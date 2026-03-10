"""Standardized API response schemas for consistent response formats."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from app.core.pydantic_compat import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = Field(description="Whether the request was successful")
    data: Optional[T] = Field(default=None, description="Response data")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


class ErrorDetail(BaseModel):
    """Error detail structure."""

    field: Optional[str] = Field(
        default=None, description="Field that caused the error"
    )
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(default=False, description="Always false for errors")
    error: Dict[str, Any] = Field(description="Error information")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    data: List[T] = Field(description="List of items")
    pagination: Dict[str, Any] = Field(description="Pagination metadata")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    next_page: Optional[int] = Field(default=None, description="Next page number")
    prev_page: Optional[int] = Field(default=None, description="Previous page number")


# Common response types
class SuccessResponse(APIResponse[Dict[str, Any]]):
    """Generic success response."""

    success: bool = Field(default=True)


class MessageResponse(APIResponse[None]):
    """Simple message response."""

    success: bool = Field(default=True)
    message: str = Field(description="Success message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = Field(default=None, description="Application version")
    checks: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed health checks"
    )


# Verification-specific responses
class VerificationResponse(APIResponse[Dict[str, Any]]):
    """Verification creation response."""

    pass


class VerificationStatusResponse(APIResponse[Dict[str, Any]]):
    """Verification status response."""

    pass


class VerificationHistoryResponse(PaginatedResponse[Dict[str, Any]]):
    """Verification history response."""

    pass


# Payment-specific responses
class PaymentInitResponse(APIResponse[Dict[str, Any]]):
    """Payment initialization response."""

    pass


class PaymentStatusResponse(APIResponse[Dict[str, Any]]):
    """Payment status response."""

    pass


class TransactionHistoryResponse(PaginatedResponse[Dict[str, Any]]):
    """Transaction history response."""

    pass


# User-specific responses
class UserProfileResponse(APIResponse[Dict[str, Any]]):
    """User profile response."""

    pass


class UserBalanceResponse(APIResponse[Dict[str, Any]]):
    """User balance response."""

    pass


# Tier-specific responses
class TierInfoResponse(APIResponse[Dict[str, Any]]):
    """Tier information response."""

    pass


class TierListResponse(APIResponse[List[Dict[str, Any]]]):
    """Tier list response."""

    pass


# Service-specific responses
class ServiceListResponse(APIResponse[List[Dict[str, Any]]]):
    """Service list response."""

    pass


class ServicePricingResponse(APIResponse[Dict[str, Any]]):
    """Service pricing response."""

    pass


# Utility functions for creating responses
def create_success_response(
    data: Any = None, message: str = None, request_id: str = None
) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
    }


def create_error_response(
    error_type: str,
    error_code: str,
    message: str,
    details: List[ErrorDetail] = None,
    request_id: str = None,
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": {
            "type": error_type,
            "code": error_code,
            "message": message,
            "details": details or [],
        },
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
    }


def create_paginated_response(
    data: List[Any], page: int, per_page: int, total: int, request_id: str = None
) -> Dict[str, Any]:
    """Create a standardized paginated response."""
    pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < pages
    has_prev = page > 1

    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_page": page + 1 if has_next else None,
            "prev_page": page - 1 if has_prev else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
    }


def create_health_response(
    status: str, version: str = None, checks: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized health response."""
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": version,
        "checks": checks,
    }


# Response status codes mapping
HTTP_STATUS_CODES = {
    "success": 200,
    "created": 201,
    "accepted": 202,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "payment_required": 402,
    "forbidden": 403,
    "not_found": 404,
    "method_not_allowed": 405,
    "conflict": 409,
    "unprocessable_entity": 422,
    "too_many_requests": 429,
    "internal_server_error": 500,
    "bad_gateway": 502,
    "service_unavailable": 503,
    "gateway_timeout": 504,
}
