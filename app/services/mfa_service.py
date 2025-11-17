"""Multi-factor authentication service."""
import base64
from io import BytesIO

import pyotp
import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class MFAService:
    @staticmethod
    def generate_secret() -> str:
        """Generate MFA secret key."""
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(user_email: str, secret: str) -> str:
        """Generate QR code for MFA setup."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Namaskah SMS"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """Verify MFA token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
