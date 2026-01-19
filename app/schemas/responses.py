"""Standardized response schemas for all API endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response."""

    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class SuccessResponse(BaseModel):
    """Standardized success response."""

    success: bool = True
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")


class PaginatedResponse(BaseModel):
    """Standardized paginated response."""

    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class ListResponse(BaseModel):
    """Standardized list response."""

    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total count")


class DataResponse(BaseModel):
    """Standardized data response."""

    success: bool = True
    data: Dict[str, Any] = Field(..., description="Response data")


class MessageResponse(BaseModel):
    """Standardized message response."""

    success: bool = True
    message: str = Field(..., description="Response message")
