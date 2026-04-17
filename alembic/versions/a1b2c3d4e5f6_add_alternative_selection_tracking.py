"""Add alternative selection tracking to purchase_outcomes

Revision ID: a1b2c3d4e5f6
Revises: e9af649b2601
Create Date: 2026-04-17

Adds two nullable columns to purchase_outcomes:
  - selected_from_alternatives: bool  — was this purchase made after user picked from alternatives UI?
  - original_request: str(10)         — what area code did they originally want before switching?

These columns power Phase 6.4 analytics (substitution pattern tracking) and the
/api/admin/analytics/learning endpoint. Data is optional and never blocks a purchase.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = 'e9af649b2601'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility (local dev fallback)
    with op.batch_alter_table('purchase_outcomes', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'selected_from_alternatives',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            )
        )
        batch_op.add_column(
            sa.Column(
                'original_request',
                sa.String(length=10),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('purchase_outcomes', schema=None) as batch_op:
        batch_op.drop_column('original_request')
        batch_op.drop_column('selected_from_alternatives')
