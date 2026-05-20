"""update_admin_email_to_vrenum

Revision ID: 794eda6caa30
Revises: add_onboarding_fields
Create Date: 2026-05-20 01:34:42.145745

"""

import bcrypt
import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "794eda6caa30"
down_revision = "add_onboarding_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update admin email from admin@namaskah.app to admin@vrenum.app"""
    conn = op.get_bind()

    # Generate new password hash for Namaskah@Admin2024
    password = "Namaskah@Admin2024"
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    # Update admin user email and password
    conn.execute(
        text(
            """
            UPDATE users
            SET email = 'admin@vrenum.app',
                password_hash = :password_hash,
                email_verified = true,
                is_admin = true,
                is_active = true,
                updated_at = NOW()
            WHERE email = 'admin@namaskah.app' OR is_admin = true
        """
        ),
        {"password_hash": password_hash},
    )

    print("✅ Admin email updated to admin@vrenum.app")


def downgrade() -> None:
    """Revert admin email back to admin@namaskah.app"""
    conn = op.get_bind()

    conn.execute(
        text(
            """
            UPDATE users
            SET email = 'admin@namaskah.app',
                updated_at = NOW()
            WHERE email = 'admin@vrenum.app' AND is_admin = true
        """
        )
    )

    print("✅ Admin email reverted to admin@namaskah.app")
