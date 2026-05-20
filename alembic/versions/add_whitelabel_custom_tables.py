"""Add whitelabel custom tables

Revision ID: add_whitelabel_custom_tables
Revises: enhance_device_tokens
Create Date: 2026-05-09 20:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_whitelabel_custom_tables"
down_revision = "enhance_device_tokens"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "whitelabel_custom_domains" not in existing_tables:
        op.create_table(
            "whitelabel_custom_domains",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("domain", sa.String(length=255), nullable=False),
            sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("verification_token", sa.String(length=255), nullable=True),
            sa.Column("verification_method", sa.String(length=50), nullable=True),
            sa.Column(
                "ssl_status",
                sa.String(length=50),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("ssl_expires_at", sa.DateTime(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_whitelabel_custom_domains_id", "whitelabel_custom_domains", ["id"]
        )
        op.create_index(
            "ix_whitelabel_custom_domains_user_id",
            "whitelabel_custom_domains",
            ["user_id"],
        )
        op.create_index(
            "ix_whitelabel_custom_domains_domain",
            "whitelabel_custom_domains",
            ["domain"],
            unique=True,
        )

    if "whitelabel_custom_branding" not in existing_tables:
        op.create_table(
            "whitelabel_custom_branding",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("logo_url", sa.String(length=500), nullable=True),
            sa.Column("favicon_url", sa.String(length=500), nullable=True),
            sa.Column(
                "primary_color",
                sa.String(length=7),
                nullable=False,
                server_default="#667eea",
            ),
            sa.Column(
                "secondary_color",
                sa.String(length=7),
                nullable=False,
                server_default="#764ba2",
            ),
            sa.Column(
                "accent_color",
                sa.String(length=7),
                nullable=False,
                server_default="#f093fb",
            ),
            sa.Column(
                "font_family",
                sa.String(length=100),
                nullable=False,
                server_default="Inter",
            ),
            sa.Column("company_name", sa.String(length=255), nullable=True),
            sa.Column("support_email", sa.String(length=255), nullable=True),
            sa.Column("support_url", sa.String(length=500), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(
            "ix_whitelabel_custom_branding_id", "whitelabel_custom_branding", ["id"]
        )
        op.create_index(
            "ix_whitelabel_custom_branding_user_id",
            "whitelabel_custom_branding",
            ["user_id"],
            unique=True,
        )

    if "whitelabel_custom_email_templates" not in existing_tables:
        op.create_table(
            "whitelabel_custom_email_templates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("template_name", sa.String(length=100), nullable=False),
            sa.Column("subject", sa.String(length=255), nullable=True),
            sa.Column("html_content", sa.Text(), nullable=True),
            sa.Column("text_content", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_whitelabel_custom_email_templates_id",
            "whitelabel_custom_email_templates",
            ["id"],
        )
        op.create_index(
            "ix_whitelabel_custom_email_templates_user_id",
            "whitelabel_custom_email_templates",
            ["user_id"],
        )


def downgrade():
    op.drop_index(
        "ix_whitelabel_custom_email_templates_user_id",
        table_name="whitelabel_custom_email_templates",
    )
    op.drop_index(
        "ix_whitelabel_custom_email_templates_id",
        table_name="whitelabel_custom_email_templates",
    )
    op.drop_table("whitelabel_custom_email_templates")

    op.drop_index(
        "ix_whitelabel_custom_branding_user_id", table_name="whitelabel_custom_branding"
    )
    op.drop_index(
        "ix_whitelabel_custom_branding_id", table_name="whitelabel_custom_branding"
    )
    op.drop_table("whitelabel_custom_branding")

    op.drop_index(
        "ix_whitelabel_custom_domains_domain", table_name="whitelabel_custom_domains"
    )
    op.drop_index(
        "ix_whitelabel_custom_domains_user_id", table_name="whitelabel_custom_domains"
    )
    op.drop_index(
        "ix_whitelabel_custom_domains_id", table_name="whitelabel_custom_domains"
    )
    op.drop_table("whitelabel_custom_domains")
