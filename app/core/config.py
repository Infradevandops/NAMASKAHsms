"""Core configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import ConfigDict

from app.core.pydantic_compat import BaseSettings, field_validator
from app.core.secrets import SecretsManager


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Basic app settings
    app_name: str = "Namaskah SMS"
    version: str = "4.4.1"
    environment: str = "development"
    debug: bool = False

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    base_url: str = "http://localhost:8000"

    # Security settings (must be set via environment variables in production)
    secret_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    @property
    def jwt_expiry_hours(self) -> int:
        return self.jwt_expiration_hours

    # Database settings
    database_url: str = "sqlite:///./namaskah.db"
    database_echo: bool = False

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    resend_api_key: Optional[str] = None
    smtp_use_tls: bool = True

    # Backward-compat aliases
    @property
    def smtp_host(self) -> str:
        return self.smtp_server

    @property
    def smtp_user(self) -> Optional[str]:
        return self.smtp_username

    @property
    def from_email(self) -> str:
        return self.smtp_username or "noreply@namaskahsms.onrender.com"

    # External API settings
    textverified_api_key: Optional[str] = None
    textverified_user_id: Optional[str] = None
    textverified_email: Optional[str] = (
        None  # used as api_username by TextVerifiedService
    )
    paystack_secret_key: Optional[str] = None
    paystack_public_key: Optional[str] = None

    # Feature flags
    enable_registration: bool = True
    enable_email_verification: bool = False
    enable_sms_forwarding: bool = True
    enable_webhooks: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 100

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS settings
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    cors_allow_credentials: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Parse CORS origins — reject wildcard in production."""
        import os

        if value == "*" and os.getenv("ENVIRONMENT", "development") == "production":
            base = os.getenv("BASE_URL", "")
            return [base] if base else []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value

    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Cache settings
    cache_ttl: int = 300  # 5 minutes

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Security headers
    enable_security_headers: bool = True
    enable_csrf_protection: bool = True

    # Session settings
    session_timeout: int = 3600  # 1 hour

    # Webhook settings
    webhook_timeout: int = 30
    webhook_retry_attempts: int = 3

    # SMS settings
    sms_provider: str = "textverified"
    sms_timeout: int = 300  # 5 minutes
    price_markup: float = 1.8

    # Payment settings
    payment_provider: str = "paystack"
    payment_webhook_timeout: int = 30
    # NGN/USD rate — update this when rate drifts significantly.
    # Last updated: March 2026. Current market rate ~1600.
    ngn_usd_rate: float = 1600.0

    # Admin settings
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None

    # Tier settings
    default_tier: str = "freemium"
    enable_tier_upgrades: bool = True

    # Notification settings
    enable_push_notifications: bool = True
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False

    # Analytics
    enable_analytics: bool = True
    analytics_retention_days: int = 90

    # Backup settings
    backup_enabled: bool = False
    backup_interval_hours: int = 24

    # SMS polling
    sms_polling_initial_interval_seconds: float = 5.0
    sms_polling_later_interval_seconds: float = 10.0
    sms_polling_max_minutes: int = 10
    sms_polling_error_backoff_seconds: float = 15.0

    # Development settings
    reload: bool = False
    workers: int = 1

    @field_validator("secret_key", "jwt_secret_key")
    @classmethod
    def validate_key_length(cls, value, info):
        """Validate secret keys are at least 32 characters in production."""
        import os

        # In production, keys must be set and at least 32 chars
        if os.getenv("ENVIRONMENT") == "production":
            if not value or len(value) < 32:
                raise ValueError(
                    "Secret keys must be at least 32 characters long and set in production"
                )

        # In development/testing, allow empty or short keys
        if value and len(value) < 32:
            # Only warn if explicitly set but too short
            if len(value) > 0:
                raise ValueError("Secret keys must be at least 32 characters long")

        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value, info=None):
        """Validate database URL format."""
        if not value:
            raise ValueError("Database URL is required")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value):
        """Validate base URL format."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return value

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
