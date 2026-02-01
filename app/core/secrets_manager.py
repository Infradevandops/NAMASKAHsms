"""AWS Secrets Manager integration for secure secrets management."""


import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.utils.exception_handling import handle_aws_exceptions, safe_json_parse

logger = logging.getLogger(__name__)


class SecretsManager:

    """Manage secrets using AWS Secrets Manager with caching."""

    def __init__(self, region_name: str = "us - east-1", cache_ttl_minutes: int = 60):

        self.region_name = region_name
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.client = None
        self._init_client()

        @handle_aws_exceptions("SecretsManager")
    def _init_client(self):

        """Initialize AWS Secrets Manager client."""
        self.client = boto3.client("secretsmanager", region_name=self.region_name)
        logger.info(f"AWS Secrets Manager client initialized for region {self.region_name}")

    def get_secret(self, secret_name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:

        """Get secret from AWS Secrets Manager with caching."""
        if not self.client:
            logger.error("Secrets Manager client not initialized")
        return None

        # Check cache
        if not force_refresh and secret_name in self.cache:
            cached = self.cache[secret_name]
        if datetime.utcnow() < cached["expires_at"]:
                logger.debug(f"Using cached secret: {secret_name}")
        return cached["value"]

        try:
            response = self.client.get_secret_value(SecretId=secret_name)

            # Parse secret value
        if "SecretString" in response:
                secret_value = safe_json_parse(response["SecretString"], {}, f"secret_{secret_name}")
        else:
                secret_value = response["SecretBinary"]

            # Cache the secret
            self.cache[secret_name] = {
                "value": secret_value,
                "expires_at": datetime.utcnow() + self.cache_ttl,
                "version": response.get("VersionId"),
            }

            logger.info(f"Retrieved secret: {secret_name}")
        return secret_value

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "ResourceNotFoundException":
                logger.warning(f"Secret not found: {secret_name}")
        else:
                logger.error(f"Failed to retrieve secret {secret_name}: {error_code} - {e}")
        return None
        except BotoCoreError as e:
            logger.error(f"AWS connection error retrieving secret {secret_name}: {e}")
        return None

    def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:

        """Create or update secret in AWS Secrets Manager."""
        if not self.client:
            logger.error("Secrets Manager client not initialized")
        return False

        try:
            secret_string = json.dumps(secret_value)

            # Try to update existing secret
        try:
                self.client.update_secret(SecretId=secret_name, SecretString=secret_string)
                logger.info(f"Updated secret: {secret_name}")
        except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Create new secret if it doesn't exist
                    self.client.create_secret(
                        Name=secret_name,
                        SecretString=secret_string,
                        Tags=[
                            {"Key": "Application", "Value": "Namaskah"},
                            {"Key": "ManagedBy", "Value": "SecretsManager"},
                        ],
                    )
                    logger.info(f"Created secret: {secret_name}")
        else:
                    raise

            # Invalidate cache
        if secret_name in self.cache:
                del self.cache[secret_name]

        return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to set secret {secret_name}: {error_code} - {e}")
        return False
        except BotoCoreError as e:
            logger.error(f"AWS connection error setting secret {secret_name}: {e}")
        return False

    def delete_secret(self, secret_name: str, recovery_window_days: int = 7) -> bool:

        """Delete secret with recovery window."""
        if not self.client:
            logger.error("Secrets Manager client not initialized")
        return False

        try:
            self.client.delete_secret(SecretId=secret_name, RecoveryWindowInDays=recovery_window_days)
            logger.info(f"Scheduled deletion of secret: {secret_name} (recovery window: {recovery_window_days} days)")

            # Invalidate cache
        if secret_name in self.cache:
                del self.cache[secret_name]

        return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to delete secret {secret_name}: {error_code} - {e}")
        return False
        except BotoCoreError as e:
            logger.error(f"AWS connection error deleting secret {secret_name}: {e}")
        return False

    def rotate_secret(self, secret_name: str, new_secret_value: Dict[str, Any]) -> bool:

        """Rotate secret by creating new version."""
        if not self.client:
            logger.error("Secrets Manager client not initialized")
        return False

        try:
            secret_string = json.dumps(new_secret_value)

            self.client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_string,
                ClientRequestToken=None,  # Let AWS generate token
            )

            logger.info(f"Rotated secret: {secret_name}")

            # Invalidate cache
        if secret_name in self.cache:
                del self.cache[secret_name]

        return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to rotate secret {secret_name}: {error_code} - {e}")
        return False
        except BotoCoreError as e:
            logger.error(f"AWS connection error rotating secret {secret_name}: {e}")
        return False

    def list_secrets(self) -> Optional[list]:

        """List all secrets."""
        if not self.client:
            logger.error("Secrets Manager client not initialized")
        return None

        try:
            response = self.client.list_secrets()
            secrets = response.get("SecretList", [])
            logger.info(f"Listed {len(secrets)} secrets")
        return secrets

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to list secrets: {error_code} - {e}")
        return None
        except BotoCoreError as e:
            logger.error(f"AWS connection error listing secrets: {e}")
        return None

    def invalidate_cache(self, secret_name: Optional[str] = None):

        """Invalidate cache for specific secret or all secrets."""
        if secret_name:
        if secret_name in self.cache:
                del self.cache[secret_name]
                logger.debug(f"Invalidated cache for secret: {secret_name}")
        else:
            self.cache.clear()
            logger.debug("Invalidated all cached secrets")

    def get_cache_stats(self) -> Dict[str, Any]:

        """Get cache statistics."""
        return {
            "cached_secrets": len(self.cache),
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60,
            "secrets": list(self.cache.keys()),
        }


# Global secrets manager instance
        _secrets_manager: Optional[SecretsManager] = None


    def get_secrets_manager(region_name: str = "us - east-1") -> SecretsManager:

        """Get or create global secrets manager instance."""
        global _secrets_manager

        if _secrets_manager is None:
        _secrets_manager = SecretsManager(region_name=region_name)

        return _secrets_manager
