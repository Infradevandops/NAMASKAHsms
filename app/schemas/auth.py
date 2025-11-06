"""Authentication request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=6, description="Password (minimum 6 characters)"
    )
    referral_code: Optional[str] = Field(None, description="Optional referral code")

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "referral_code": "ABC123",
            }
        }
    }


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(None, min_length=6, description="New password")

    @validator("password")
    def validate_password(cls, v):
        if v and len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str
    email: str
    credits: float
    free_verifications: float
    is_admin: bool
    email_verified: bool
    referral_code: str
    created_at: datetime
    provider: Optional[str] = "email"
    avatar_url: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "user_1642680000000",
                "email": "user@example.com",
                "credits": 10.5,
                "free_verifications": 1.0,
                "is_admin": False,
                "email_verified": True,
                "referral_code": "ABC123",
                "created_at": "2024-01-20T10:00:00Z",
            }
        },
    }


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "securepassword123"}
        }
    }


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "user_1642680000000",
                    "email": "user@example.com",
                    "credits": 10.5,
                    "free_verifications": 1.0,
                    "is_admin": False,
                    "email_verified": True,
                    "referral_code": "ABC123",
                    "created_at": "2024-01-20T10:00:00Z",
                },
            }
        }
    }


class APIKeyCreate(BaseModel):
    """Schema for API key creation."""

    name: str = Field(..., min_length=1, max_length=100, description="API key name")

    model_config = {"json_schema_extra": {"example": {"name": "Production API Key"}}}


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: str
    name: str
    key: str = Field(..., description="API key (shown only once)")
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "key_1642680000000",
                "name": "Production API Key",
                "key": "nsk_abc123def456...",
                "is_active": True,
                "created_at": "2024-01-20T10:00:00Z",
                "last_used": None,
            }
        },
    }


class APIKeyListResponse(BaseModel):
    """Schema for API key list (without actual key)."""

    id: str
    name: str
    key_preview: str = Field(..., description="Masked API key")
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "key_1642680000000",
                "name": "Production API Key",
                "key_preview": "nsk_abc123...def456",
                "is_active": True,
                "created_at": "2024-01-20T10:00:00Z",
                "last_used": "2024-01-20T15:30:00Z",
            }
        }
    }


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="Email address for password reset")

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com"}}}


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password")

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "reset_token_abc123",
                "new_password": "newsecurepassword123",
            }
        }
    }


class EmailVerificationRequest(BaseModel):
    """Schema for email verification resend."""

    email: EmailStr = Field(..., description="Email address to verify")


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication."""

    token: str = Field(..., description="Google OAuth token")

    model_config = {
        "json_schema_extra": {"example": {"token": "google_oauth_token_here"}}
    }
