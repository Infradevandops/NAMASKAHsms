"""Add MFA fields to users table

Revision ID: add_mfa_fields
Revises: add_terms_accepted
Create Date: 2026-05-06
"""

revision = "add_mfa_fields"
down_revision = "add_terms_accepted"
branch_labels = None
depends_on = None


def upgrade():
    import sqlalchemy as sa

    from alembic import op

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "mfa_secret" not in columns:
        op.add_column("users", sa.Column("mfa_secret", sa.String(64), nullable=True))
    if "mfa_enabled" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "mfa_enabled", sa.Boolean(), nullable=False, server_default="false"
            ),
        )


def downgrade():
    from alembic import op

    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
