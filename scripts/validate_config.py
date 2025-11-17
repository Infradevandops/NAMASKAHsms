#!/usr/bin/env python3
"""
Production Configuration Validation Script
Validates all required configuration before deployment.
"""
import os
import secrets
import sys
from urllib.parse import urlparse

from app.core.config import Settings

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class ConfigValidator:
    """Comprehensive configuration validator for production deployment."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.settings = None

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating production configuration...")

        try:
            # Load settings
            self.settings = Settings()
            print(
                f"✅ Configuration loaded for environment: {self.settings.environment}"
            )

            # Run validation checks
            self._validate_environment()
            self._validate_security_keys()
            self._validate_database_config()
            self._validate_redis_config()
            self._validate_external_apis()
            self._validate_ssl_config()
            self._validate_monitoring_config()

            # Print results
            self._print_results()

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Failed to load configuration: {str(e)}")
            self._print_results()
            return False

    def _validate_environment(self):
        """Validate environment-specific settings."""
        if self.settings.environment not in ["development", "staging", "production"]:
            self.errors.append(f"Invalid environment: {self.settings.environment}")

        if self.settings.environment == "production":
            if self.settings.debug:
                self.errors.append("Debug mode must be disabled in production")

            if not self.settings.base_url.startswith("https://"):
                self.errors.append("Production requires HTTPS base URL")

        print(f"✅ Environment validation: {self.settings.environment}")

    def _validate_security_keys(self):
        """Validate security keys and secrets."""
        # Check secret key
        if not self.settings.secret_key or len(self.settings.secret_key) < 32:
            self.errors.append("SECRET_KEY must be at least 32 characters")
        elif self.settings.secret_key in ["your-secure-secret-key", "change-me"]:
            self.errors.append("SECRET_KEY contains placeholder value")

        # Check JWT secret key
        if not self.settings.jwt_secret_key or len(self.settings.jwt_secret_key) < 32:
            self.errors.append("JWT_SECRET_KEY must be at least 32 characters")
        elif self.settings.jwt_secret_key in ["your-jwt-secret-key", "change-me"]:
            self.errors.append("JWT_SECRET_KEY contains placeholder value")

        # Check if keys are different
        if self.settings.secret_key == self.settings.jwt_secret_key:
            self.warnings.append("SECRET_KEY and JWT_SECRET_KEY should be different")

        print("✅ Security keys validation completed")

    def _validate_database_config(self):
        """Validate database configuration."""
        if not self.settings.database_url:
            self.errors.append("DATABASE_URL is required")
            return

        # Parse database URL
        try:
            parsed = urlparse(self.settings.database_url)

            if self.settings.environment == "production":
                if parsed.scheme not in ["postgresql", "postgresql+asyncpg"]:
                    self.errors.append("Production requires PostgreSQL database")

                if not parsed.hostname or not parsed.username:
                    self.errors.append("Database URL missing hostname or username")

                if parsed.password in ["password", "secure_password", None]:
                    self.errors.append("Database password is weak or missing")

            # Validate pool settings
            if self.settings.database_pool_size < 5:
                self.warnings.append("Database pool size is very small for production")

            if self.settings.database_pool_size > 50:
                self.warnings.append("Database pool size is very large")

        except Exception as e:
            self.errors.append(f"Invalid database URL format: {str(e)}")

        print("✅ Database configuration validation completed")

    def _validate_redis_config(self):
        """Validate Redis configuration."""
        if not self.settings.redis_url:
            self.warnings.append("Redis URL not configured - caching will be disabled")
            return

        try:
            parsed = urlparse(self.settings.redis_url)

            if parsed.scheme != "redis":
                self.errors.append("Invalid Redis URL scheme")

            if not parsed.hostname:
                self.errors.append("Redis hostname is required")

            if self.settings.redis_max_connections < 10:
                self.warnings.append("Redis connection pool is small for production")

        except Exception as e:
            self.errors.append(f"Invalid Redis URL format: {str(e)}")

        print("✅ Redis configuration validation completed")

    def _validate_external_apis(self):
        """Validate external API configurations."""
        # TextVerified API
        if not self.settings.textverified_api_key:
            self.errors.append("TEXTVERIFIED_API_KEY is required")
        elif "your-textverified" in self.settings.textverified_api_key:
            self.errors.append("TEXTVERIFIED_API_KEY contains placeholder value")

        # Paystack API
        if not self.settings.paystack_secret_key:
            self.errors.append("PAYSTACK_SECRET_KEY is required")
        elif "your-paystack" in self.settings.paystack_secret_key:
            self.errors.append("PAYSTACK_SECRET_KEY contains placeholder value")

        # Check for test vs live keys in production
        if self.settings.environment == "production":
            if (
                self.settings.paystack_secret_key
                and not self.settings.paystack_secret_key.startswith("sk_live_")
            ):
                self.errors.append(
                    "Production requires live Paystack secret key (sk_live_)"
                )

        print("✅ External API validation completed")

    def _validate_ssl_config(self):
        """Validate SSL/TLS configuration."""
        if self.settings.environment == "production":
            if self.settings.ssl_cert_path and not os.path.exists(
                self.settings.ssl_cert_path
            ):
                self.errors.append(
                    f"SSL certificate file not found: {self.settings.ssl_cert_path}"
                )

            if self.settings.ssl_key_path and not os.path.exists(
                self.settings.ssl_key_path
            ):
                self.errors.append(
                    f"SSL private key file not found: {self.settings.ssl_key_path}"
                )

        print("✅ SSL configuration validation completed")

    def _validate_monitoring_config(self):
        """Validate monitoring and observability configuration."""
        if self.settings.environment == "production":
            if not self.settings.sentry_dsn:
                self.warnings.append(
                    "Sentry DSN not configured - error tracking disabled"
                )

            if not self.settings.google_analytics_id:
                self.warnings.append("Google Analytics not configured")

        print("✅ Monitoring configuration validation completed")

    def _print_results(self):
        """Print validation results."""
        print("\n" + "=" * 60)
        print("📋 CONFIGURATION VALIDATION RESULTS")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All configuration checks passed!")
        elif not self.errors:
            print(f"\n✅ Configuration is valid with {len(self.warnings)} warnings")
        else:
            print(f"\n❌ Configuration validation failed with {len(self.errors)} errors")

        print("=" * 60)


def generate_secure_keys():
    """Generate secure keys for production."""
    print("\n🔐 Generating secure keys for production:")
    print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
    print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")


def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate production configuration")
    parser.add_argument(
        "--generate-keys", action="store_true", help="Generate secure keys"
    )
    parser.add_argument(
        "--env-file", default=".env.production", help="Environment file to validate"
    )

    args = parser.parse_args()

    if args.generate_keys:
        generate_secure_keys()
        return

    # Set environment file
    os.environ.setdefault("ENV_FILE", args.env_file)

    # Run validation
    validator = ConfigValidator()
    success = validator.validate_all()

    if success:
        print("\n🚀 Configuration is ready for production deployment!")
        sys.exit(0)
    else:
        print("\n🛑 Configuration validation failed. Fix errors before deployment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
