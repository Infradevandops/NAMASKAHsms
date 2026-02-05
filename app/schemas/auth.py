"""Authentication and user schemas."""

from datetime import datetime
from typing import Optional
from pydantic import EmailStr
from app.core.pydantic_compat import BaseModel, Field, field_validator
from app.schemas.validators import validate_email, validate_password_strength


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    referral_code: Optional[str] = Field(None, description="Referral code")

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_field(cls, v):
        return validate_email(v)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password_field(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        return validate_password_strength(v)

    @field_validator("referral_code", mode="before")
    @classmethod
    def validate_referral_field(cls, v):
        if v and len(v) != 6:
            raise ValueError("Referral code must be 6 characters")
        return v.upper() if v else v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "referral_code": "ABC123"
            }
        }
    }


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    }


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(None, min_length=6, description="New password")

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v):
        if v and len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    tier: str = Field(..., description="User tier")
    credits: float = Field(..., description="User credits")
    created_at: datetime = Field(..., description="Account creation date")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "user_123",
                "email": "user@example.com",
                "tier": "pro",
                "credits": 25.50,
                "created_at": "2024-01-20T10:00:00Z"
            }
        }
    }


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 2592000
            }
        }
    }


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="User email address")

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com"}
        }
    }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password", mode="before")
    @classmethod
    def validate_new_password(cls, v):
        return validate_password_strength(v)

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "reset_token_123",
                "new_password": "NewSecurePass123!"
            }
        }
    }


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""

    email: EmailStr = Field(..., description="Email to verify")

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com"}
        }
    }


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication."""

    id_token: str = Field(..., description="Google ID token")

    model_config = {
        "json_schema_extra": {
            "example": {"id_token": "google_id_token_here"}
        }
    }


class APIKeyCreate(BaseModel):
    """Schema for API key creation."""

    name: str = Field(..., min_length=3, max_length=50, description="API key name")

    model_config = {
        "json_schema_extra": {
            "example": {"name": "My API Key"}
        }
    }


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key: str = Field(..., description="API key value")
    created_at: datetime = Field(..., description="Creation date")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "key_123",
                "name": "My API Key",
                "key": "nsk_live_1234567890abcdef",
                "created_at": "2024-01-20T10:00:00Z"
            }
        }
    }


class APIKeyListResponse(BaseModel):
    """Schema for API key list response."""

    keys: list[APIKeyResponse] = Field(..., description="List of API keys")
    total: int = Field(..., description="Total number of keys")

    model_config = {
        "json_schema_extra": {
            "example": {
                "keys": [],
                "total": 0
            }
        }
    }
