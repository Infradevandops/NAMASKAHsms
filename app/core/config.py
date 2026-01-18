"""Core configuration management using Pydantic Settings."""

import os
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Namaskah SMS"
    app_version: str = "2.4.0"
    debug: bool = False
    environment: str = "development"

    # Security
    secret_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    # jwt_expire_minutes removed here to avoid duplicate; see JWT Settings section below

    # Server Configuration
    host: str = "127.0.0.1"  # Default to localhost for security
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = "sqlite:///./sms.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # SMS Providers
    # SMS - Activate API
    sms_activate_api_key: Optional[str] = None

    # GetSMS API
    getsms_api_key: Optional[str] = None

    # Crypto Wallet Configuration
    crypto_btc_address: Optional[str] = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    crypto_eth_address: Optional[str] = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    crypto_sol_address: Optional[str] = "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH"
    crypto_ltc_address: Optional[str] = "ltc1qrg5u5x4j8e4w9y2kgdygjrsqtzq2n0yrf249l7"

    # WhatsApp Business API
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None

    # Telegram Bot API
    telegram_bot_token: Optional[str] = None

    # TextVerified API
    textverified_api_key: Optional[str] = None
    textverified_email: Optional[str] = None

    # JWT Settings
    # JWT Settings
    # Default JWT expiration set to 24 hours for better UX in production.
    # Keep both minute and hour representations for backward compatibility.
    jwt_expire_minutes: int = 1440  # 24 hours
    jwt_expiry_hours: int = 24  # 24 hours

    # HTTP Client timeouts (seconds)
    http_timeout_seconds: float = 30.0
    http_connect_timeout_seconds: float = 5.0
    http_read_timeout_seconds: float = 25.0

    # Background task timeout (seconds) — used to bound long - running background services
    async_task_timeout_seconds: int = 1800  # 30 minutes

    # SMS polling configuration
    sms_polling_max_minutes: int = 20  # Poll for up to 20 minutes (recommended)
    sms_polling_initial_interval_seconds: int = 5
    sms_polling_later_interval_seconds: int = 10
    sms_polling_error_backoff_seconds: int = 15

    # Voice polling configuration
    voice_polling_interval_seconds: int = 5
    voice_polling_timeout_minutes: int = 5
    voice_estimated_cost: float = 3.50
    voice_max_retry_attempts: int = 3

    # Paystack
    paystack_secret_key: Optional[str] = None
    paystack_public_key: Optional[str] = None

    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@namaskah.app"

    # Application URLs
    base_url: str = "http://localhost:8000"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Monitoring
    sentry_dsn: Optional[str] = None
    google_analytics_id: Optional[str] = None

    # SSL/TLS
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None

    @field_validator("secret_key", "jwt_secret_key")
    @classmethod
    def validate_key_length(cls, value):
        """Validate secret keys are at least 32 characters."""
        if value and len(value) < 32:
            raise ValueError("Secret keys must be at least 32 characters long")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value, info=None):
        """Validate database URL format."""
        if not value:
            raise ValueError("Database URL is required")

        # Check for production database requirements
        if info and hasattr(info, "data"):
            environment = info.data.get("environment", "development")
            if value.startswith("sqlite://") and environment == "production":
                raise ValueError("SQLite is not recommended for production. Use PostgreSQL.")

        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value):
        """Validate base URL format."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return value

    def __init__(self, **kwargs):
        import secrets
        
        # Pydantic reads from env during super().__init__
        # but we need to know if they were provided to decide if we auto-generate
        env_secret = kwargs.get("secret_key") or os.getenv("SECRET_KEY")
        env_jwt_secret = kwargs.get("jwt_secret_key") or os.getenv("JWT_SECRET_KEY")
        
        environment = kwargs.get("environment") or os.getenv("ENVIRONMENT", "development")

        if environment == "production":
            if not env_secret:
                raise ValueError("SECRET_KEY is required in production environment")
            if not env_jwt_secret:
                raise ValueError("JWT_SECRET_KEY is required in production environment")
        else:
            if not env_secret:
                kwargs["secret_key"] = secrets.token_urlsafe(32)
            if not env_jwt_secret:
                kwargs["jwt_secret_key"] = secrets.token_urlsafe(32)

        super().__init__(**kwargs)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def validate_production_config(self) -> None:
        """Validate production - specific configuration."""
        if not self.is_production():
            return

        required_production_settings = [
            ("database_url", "DATABASE_URL"),
            ("paystack_secret_key", "PAYSTACK_SECRET_KEY"),
        ]

        missing_settings = []
        for attr, env_var in required_production_settings:
            value = getattr(self, attr)
            if not value or value in ["your-", "change - me", "placeholder"]:
                missing_settings.append(env_var)

        if missing_settings:
            raise ValueError(
                f"Production environment requires these settings: {', '.join(missing_settings)}"
            )

        # Validate HTTPS in production
        if not self.base_url.startswith("https://"):
            raise ValueError("Production environment requires HTTPS base URL")

        # Validate database is PostgreSQL
        if not self.database_url.startswith("postgresql://"):
            raise ValueError("Production environment requires PostgreSQL database")

        # Note: Host binding validation removed for cloud deployment compatibility
        # Cloud platforms and containers handle networking securely at the infrastructure level

    model_config = {
        "env_file": [
            ".env.local",  # Highest priority (local overrides)
            ".env",  # Main environment file
            ".env.development",  # Fallback for development
        ],
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with validation."""
    settings_instance = Settings()

    # Validate secrets on startup (production only)
    if settings_instance.environment == "production":
        try:
            from app.core.secrets import SecretsManager
            SecretsManager.validate_required_secrets(settings_instance.environment)
        except Exception:
             pass

    # Validate production configuration
    settings_instance.validate_production_config()

    return settings_instance


# Legacy settings instance for backward compatibility
settings = get_settings()
