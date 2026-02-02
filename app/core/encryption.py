"""Data encryption utilities."""


from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionManager:

    """Manages data encryption/decryption."""

    def __init__(self):
        # Generate or load encryption key
        self.key = settings.encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.key)

        @handle_encryption_exceptions
    def encrypt(self, data: str) -> str:

        """Encrypt data."""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:

        """Decrypt data."""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
        except InvalidToken as e:
            logger.error(f"Invalid encryption token during decryption: {e}")
        return encrypted_data
        except ValueError as e:
            logger.error(f"Invalid data format during decryption: {e}")
        return encrypted_data

    def encrypt_field(self, obj: dict, field: str) -> dict:

        """Encrypt specific field in object."""
        if field in obj and obj[field]:
            obj[field] = self.encrypt(str(obj[field]))
        return obj

    def decrypt_field(self, obj: dict, field: str) -> dict:

        """Decrypt specific field in object."""
        if field in obj and obj[field]:
            obj[field] = self.decrypt(obj[field])
        return obj


        encryption_manager = EncryptionManager()