"""
Input Validation Schemas
Pydantic models for request validation
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
import re


class PaymentRequest(BaseModel):
    """Payment initialization request"""
    amount: float = Field(gt=0, le=10000, description="Amount in USD")
    
    @validator('amount')
    def validate_amount(cls, v):
        # Must be multiple of 0.01
        if round(v, 2) != v:
            raise ValueError('Amount must have max 2 decimal places')
        if v < 1.0:
            raise ValueError('Minimum amount is $1.00')
        return v


class VerificationRequest(BaseModel):
    """SMS verification request"""
    service: str = Field(min_length=2, max_length=50)
    country: str = Field(regex="^[A-Z]{2}$", description="ISO 3166-1 alpha-2 country code")
    capability: str = Field(default="sms", regex="^(sms|voice)$")
    
    @validator('service')
    def validate_service(cls, v):
        # Whitelist of allowed services
        allowed = ['whatsapp', 'telegram', 'facebook', 'google', 'twitter', 'instagram']
        if v.lower() not in allowed:
            raise ValueError(f'Service must be one of: {", ".join(allowed)}')
        return v.lower()


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        # Must contain uppercase, lowercase, digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for common passwords
        common = ['password', '12345678', 'qwerty', 'admin']
        if v.lower() in common:
            raise ValueError('Password is too common')
        
        return v
    
    @validator('full_name')
    def validate_name(cls, v):
        if v and not re.match(r'^[a-zA-Z\s\'-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class WalletOperationRequest(BaseModel):
    """Wallet credit/debit request"""
    amount: float = Field(gt=0, le=10000)
    description: Optional[str] = Field(None, max_length=200)
    
    @validator('amount')
    def validate_amount(cls, v):
        if round(v, 2) != v:
            raise ValueError('Amount must have max 2 decimal places')
        return v


class APIKeyRequest(BaseModel):
    """API key generation request"""
    name: str = Field(min_length=3, max_length=50)
    permissions: list[str] = Field(default=["read"])
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v
    
    @validator('permissions')
    def validate_permissions(cls, v):
        allowed = ['read', 'write', 'admin']
        for perm in v:
            if perm not in allowed:
                raise ValueError(f'Invalid permission: {perm}')
        return v


class UpdateProfileRequest(BaseModel):
    """Profile update request"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    
    @validator('full_name')
    def validate_name(cls, v):
        if v and not re.match(r'^[a-zA-Z\s\'-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v


# Sanitization helpers
def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not value:
        return value
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Trim to max length
    value = value[:max_length]
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    return value


def sanitize_html(value: str) -> str:
    """Remove HTML tags from input"""
    import html
    # Escape HTML entities
    value = html.escape(value)
    # Remove any remaining tags
    value = re.sub(r'<[^>]+>', '', value)
    return value
