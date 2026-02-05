"""Secrets management utilities."""

import os
from typing import Optional, Dict, Any


class SecretsManager:
    """Centralized secrets management."""
    
    # List of sensitive key patterns
    SENSITIVE_KEYS = [
        "PASSWORD", "SECRET", "KEY", "TOKEN", "API_KEY",
        "PRIVATE", "CREDENTIAL", "AUTH", "CERT", "SIGNATURE"
    ]
    
    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """Get secret from environment with validation."""
        value = os.getenv(key, default)
        if not value:
            raise ValueError(f"Required secret {key} not found")
        return value

    @staticmethod
    def is_sensitive_key(key: str) -> bool:
        """Check if a key contains sensitive information."""
        key_upper = key.upper()
        return any(sensitive in key_upper for sensitive in SecretsManager.SENSITIVE_KEYS)

    @staticmethod
    def mask_secret(value: str, visible_chars: int = 4) -> str:
        """Mask sensitive values for logging."""
        if len(value) <= visible_chars * 2:
            return "*" * len(value)
        return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]

    @staticmethod
    def validate_secrets(config_dict: Dict[str, Any]) -> Dict[str, str]:
        """Validate and mask secrets in configuration."""
        issues = {}
        
        for key, value in config_dict.items():
            if SecretsManager.is_sensitive_key(key):
                if not value or (isinstance(value, str) and len(value) < 8):
                    issues[key] = f"Secret {key} is too short or missing"
        
        return issues

    @staticmethod
    def get_masked_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration with sensitive values masked."""
        masked = {}
        
        for key, value in config_dict.items():
            if SecretsManager.is_sensitive_key(key) and isinstance(value, str):
                masked[key] = SecretsManager.mask_secret(value)
            else:
                masked[key] = value
        
        return masked