"""Secrets management for production security."""


import logging
import os
import secrets
from pathlib import Path
from typing import Dict, Optional
from app.utils.path_security import sanitize_filename, validate_safe_path

logger = logging.getLogger(__name__)


class SecretsManager:

    """Secure secrets management with validation."""

    # Environment - specific required secrets
    REQUIRED_SECRETS = {
        "development": ["SECRET_KEY", "JWT_SECRET_KEY"],
        "test": ["SECRET_KEY", "JWT_SECRET_KEY"],
        "staging": [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "TEXTVERIFIED_API_KEY",
        ],
        "production": [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "TEXTVERIFIED_API_KEY",
            "PAYSTACK_SECRET_KEY",
        ],
    }

    # Secrets that should never be logged or exposed
    SENSITIVE_KEYS = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "PASSWORD",
        "API_KEY",
        "TOKEN",
        "PRIVATE_KEY",
        "CERT",
        "CREDENTIAL",
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
        return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars * 2)}{value[-visible_chars:]}"

        @staticmethod
    def validate_required_secrets(environment: str = None) -> None:
        """Validate all required secrets are present for the environment."""
        if not environment:
            environment = os.getenv("ENVIRONMENT", "development")

        required_secrets = SecretsManager.REQUIRED_SECRETS.get(environment, [])
        missing = []

        logger.info(f"Checking secrets for environment: {environment}")
        for key in required_secrets:
            value = os.getenv(key)
            logger.info(f"Checking {key}: {'FOUND' if value else 'MISSING'}")
        if not value:
                # Auto - generate certain keys if missing
        if key in ["SECRET_KEY", "JWT_SECRET_KEY"]:
                    generated_key = SecretsManager.generate_secret_key()
                    os.environ[key] = generated_key
                    logger.warning(f"Generated {key} for {environment} environment")
                else:
                    missing.append(key)
            elif SecretsManager.is_weak_secret(value):
                logger.warning(f"{key} appears to be a weak or default value")

        if missing:
            raise ValueError(f"Missing required secrets for {environment}: {missing}")

        @staticmethod
    def is_weak_secret(value: str) -> bool:
        """Check if a secret appears to be weak or default."""
        weak_patterns = [
            "password",
            "123456",
            "admin",
            "test",
            "default",
            "changeme",
            "secret",
            "key",
            "your-",
            "placeholder",
        ]
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in weak_patterns) or len(value) < 16

        @staticmethod
    def generate_secret_key() -> str:
        """Generate secure 256 - bit secret key."""
        return secrets.token_urlsafe(32)

        @staticmethod
    def generate_all_keys() -> Dict[str, str]:
        """Generate all required keys for a new environment."""
        return {
            "SECRET_KEY": SecretsManager.generate_secret_key(),
            "JWT_SECRET_KEY": SecretsManager.generate_secret_key(),
        }

        @staticmethod
    def create_env_file(environment: str, output_path: str = None) -> str:
        """Create a new environment file with generated secrets."""
        if not output_path:
            output_path = f".env.{environment}"

        keys = SecretsManager.generate_all_keys()

        timestamp = secrets.token_hex(8)
        env_content = (
            f"# Generated environment file for {environment}\n"
            + f"# Generated on: {timestamp}\n"
            + "# \n"
            + "# IMPORTANT: Keep this file secure and never commit to version control\n\n"
            + f"ENVIRONMENT={environment}\n"
            + f"SECRET_KEY={keys['SECRET_KEY']}\n"
            + f"JWT_SECRET_KEY={keys['JWT_SECRET_KEY']}\n\n"
            + "# Add your other environment-specific variables below:\n"
            + "# DATABASE_URL=your-database-url\n"
            + "# TEXTVERIFIED_API_KEY=your-api-key\n"
            + "# PAYSTACK_SECRET_KEY=your-paystack-key\n"
        )

        # Validate output path to prevent path traversal
        safe_filename = sanitize_filename(os.path.basename(output_path))
        safe_path = validate_safe_path(safe_filename, Path.cwd())

        safe_path.write_text(env_content)
        return str(safe_path)

        @staticmethod
    def audit_environment() -> Dict[str, any]:
        """Audit current environment for security issues."""
        issues = []
        warnings = []

        environment = os.getenv("ENVIRONMENT", "development")

        # Check for required secrets
        required_secrets = SecretsManager.REQUIRED_SECRETS.get(environment, [])

        for key in required_secrets:
            value = os.getenv(key)
        if not value:
                issues.append(f"Missing required secret: {key}")
            elif SecretsManager.is_weak_secret(value):
                warnings.append(f"Weak secret detected: {key}")

        # Check for exposed secrets in wrong environment
        if environment == "production":
            paystack_key = os.getenv("PAYSTACK_SECRET_KEY", "")
            base_url = os.getenv("BASE_URL", "")
        if "test" in paystack_key.lower():
                warnings.append("Test Paystack key detected in production")
        if "localhost" in base_url:
                warnings.append("Localhost URL detected in production")

        return {
            "environment": environment,
            "issues": issues,
            "warnings": warnings,
            "secrets_count": len([k for k in os.environ if SecretsManager.is_sensitive_key(k)]),
        }
