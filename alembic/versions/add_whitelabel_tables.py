"""Add whitelabel tables

Revision ID: add_whitelabel_tables
Revises: enhance_device_tokens
Create Date: 2026-05-07

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_whitelabel_tables"
down_revision = "enhance_device_tokens"
branch_labels = None
depends_on = None


def upgrade():
    # Create whitelabel_domains table
    op.create_table(
        "whitelabel_domains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column(
            "ssl_status", sa.String(50), nullable=False, server_default="pending"
        ),
        sa.Column("ssl_expires_at", sa.DateTime(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index("ix_whitelabel_domains_domain", "whitelabel_domains", ["domain"])
    op.create_index("ix_whitelabel_domains_user_id", "whitelabel_domains", ["user_id"])

    # Create whitelabel_branding table
    op.create_table(
        "whitelabel_branding",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),
        sa.Column(
            "primary_color", sa.String(7), nullable=False, server_default="#667eea"
        ),
        sa.Column(
            "secondary_color", sa.String(7), nullable=False, server_default="#764ba2"
        ),
        sa.Column(
            "accent_color", sa.String(7), nullable=False, server_default="#f093fb"
        ),
        sa.Column(
            "font_family", sa.String(100), nullable=False, server_default="Inter"
        ),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("support_email", sa.String(255), nullable=True),
        sa.Column("support_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_whitelabel_branding_user_id", "whitelabel_branding", ["user_id"]
    )

    # Create whitelabel_email_templates table
    op.create_table(
        "whitelabel_email_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_name", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "template_name", name="uq_user_template"),
    )
    op.create_index(
        "ix_whitelabel_email_templates_user_id",
        "whitelabel_email_templates",
        ["user_id"],
    )


def downgrade():
    op.drop_index(
        "ix_whitelabel_email_templates_user_id", table_name="whitelabel_email_templates"
    )
    op.drop_table("whitelabel_email_templates")

    op.drop_index("ix_whitelabel_branding_user_id", table_name="whitelabel_branding")
    op.drop_table("whitelabel_branding")

    op.drop_index("ix_whitelabel_domains_user_id", table_name="whitelabel_domains")
    op.drop_index("ix_whitelabel_domains_domain", table_name="whitelabel_domains")
    op.drop_table("whitelabel_domains")
