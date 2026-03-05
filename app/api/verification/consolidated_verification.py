"""Stub module — re-exports for backward compatibility."""
from app.schemas.verification import VerificationCreate
from app.utils.data_masking import create_safe_error_detail
from app.api.verification.router import router

__all__ = ["VerificationCreate", "create_safe_error_detail", "router"]
