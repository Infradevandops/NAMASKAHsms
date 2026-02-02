"""Configuration loader with AWS Secrets Manager integration."""


import logging
from typing import Any, Dict, Optional
from app.core.config import Settings

logger = logging.getLogger(__name__)


class ConfigWithSecrets:

    """Load configuration from environment and AWS Secrets Manager."""

    def __init__(self, settings: Settings, use_secrets_manager: bool = True):

        self.settings = settings
        self.use_secrets_manager = use_secrets_manager
        self.secrets_manager = get_secrets_manager() if use_secrets_manager else None
        self.audit = get_audit()

    def get_secret(

        self,
        secret_name: str,
        key: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        ) -> Optional[Any]:
        """Get secret from AWS Secrets Manager with audit logging."""
        if not self.use_secrets_manager or not self.secrets_manager:
            logger.warning(f"Secrets Manager not available for {secret_name}")
        return None

        try:
            secret_value = self.secrets_manager.get_secret(secret_name)

        if secret_value is None:
                self.audit.log_error(
                    action="get",
                    secret_name=secret_name,
                    error="Secret not found",
                    user_id=user_id,
                    ip_address=ip_address,
                )
        return None

            # Extract specific key if provided
        if key and isinstance(secret_value, dict):
                result = secret_value.get(key)
        else:
                result = secret_value

            # Log successful retrieval
            self.audit.log_get(secret_name=secret_name, user_id=user_id, ip_address=ip_address)

        return result

        except Exception as e:
            self.audit.log_error(
                action="get",
                secret_name=secret_name,
                error=str(e),
                user_id=user_id,
                ip_address=ip_address,
            )
            logger.error(f"Failed to get secret {secret_name}: {e}")
        return None

    def load_provider_secrets(self, user_id: Optional[str] = None) -> Dict[str, Any]:

        """Load all SMS provider secrets."""
        providers = {}

        provider_configs = {
            "textverified": ["api_key", "email"],
            "fivesim": ["api_key", "email"],
            "sms_activate": ["api_key"],
            "getsms": ["api_key"],
        }

        for provider_name, keys in provider_configs.items():
            secret_name = f"namaskah/{provider_name}"
            secret_value = self.get_secret(secret_name, user_id=user_id)

        if secret_value:
                providers[provider_name] = secret_value

        return providers

    def load_payment_secrets(self, user_id: Optional[str] = None) -> Dict[str, Any]:

        """Load payment provider secrets."""
        payment_secrets = {}

        payment_providers = {
            "paystack": ["public_key", "secret_key"],
            "stripe": ["public_key", "secret_key"],
        }

        for provider_name, keys in payment_providers.items():
            secret_name = f"namaskah/payment/{provider_name}"
            secret_value = self.get_secret(secret_name, user_id=user_id)

        if secret_value:
                payment_secrets[provider_name] = secret_value

        return payment_secrets

    def load_oauth_secrets(self, user_id: Optional[str] = None) -> Dict[str, Any]:

        """Load OAuth provider secrets."""
        oauth_secrets = {}

        oauth_providers = {
            "google": ["client_id", "client_secret"],
            "github": ["client_id", "client_secret"],
        }

        for provider_name, keys in oauth_providers.items():
            secret_name = f"namaskah/oauth/{provider_name}"
            secret_value = self.get_secret(secret_name, user_id=user_id)

        if secret_value:
                oauth_secrets[provider_name] = secret_value

        return oauth_secrets

    def update_secret(

        self,
        secret_name: str,
        secret_value: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        ) -> bool:
        """Update secret in AWS Secrets Manager."""
        if not self.use_secrets_manager or not self.secrets_manager:
            logger.warning(f"Secrets Manager not available for {secret_name}")
        return False

        try:
            success = self.secrets_manager.set_secret(secret_name, secret_value)

        if success:
                self.audit.log_set(secret_name=secret_name, user_id=user_id, ip_address=ip_address)
        else:
                self.audit.log_error(
                    action="set",
                    secret_name=secret_name,
                    error="Failed to update secret",
                    user_id=user_id,
                    ip_address=ip_address,
                )

        return success

        except Exception as e:
            self.audit.log_error(
                action="set",
                secret_name=secret_name,
                error=str(e),
                user_id=user_id,
                ip_address=ip_address,
            )
            logger.error(f"Failed to update secret {secret_name}: {e}")
        return False

    def rotate_secret(

        self,
        secret_name: str,
        new_secret_value: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        ) -> bool:
        """Rotate secret."""
        if not self.use_secrets_manager or not self.secrets_manager:
            logger.warning(f"Secrets Manager not available for {secret_name}")
        return False

        try:
            success = self.secrets_manager.rotate_secret(secret_name, new_secret_value)

        if success:
                self.audit.log_rotate(secret_name=secret_name, user_id=user_id, ip_address=ip_address)
        else:
                self.audit.log_error(
                    action="rotate",
                    secret_name=secret_name,
                    error="Failed to rotate secret",
                    user_id=user_id,
                    ip_address=ip_address,
                )

        return success

        except Exception as e:
            self.audit.log_error(
                action="rotate",
                secret_name=secret_name,
                error=str(e),
                user_id=user_id,
                ip_address=ip_address,
            )
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
        return False


    def get_config_with_secrets(settings: Settings) -> ConfigWithSecrets:

        """Get configuration loader with secrets manager."""
        return ConfigWithSecrets(settings)