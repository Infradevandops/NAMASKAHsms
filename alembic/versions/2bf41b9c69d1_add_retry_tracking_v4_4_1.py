"""add_retry_tracking_v4_4_1

Revision ID: 2bf41b9c69d1
Revises: 6773ecc277a0
Create Date: 2026-03-17 23:44:26.652055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bf41b9c69d1'
down_revision = '6773ecc277a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("verifications")]

    new_cols = [
        ("retry_attempts", sa.Integer(), False, "0"),
        ("area_code_matched", sa.Boolean(), False, "true"),
        ("carrier_matched", sa.Boolean(), False, "true"),
        ("real_carrier", sa.String(), True, None),
        ("carrier_surcharge", sa.Float(), False, "0.0"),
        ("area_code_surcharge", sa.Float(), False, "0.0"),
        ("voip_rejected", sa.Boolean(), False, "false"),
    ]
    for name, col_type, nullable, default in new_cols:
        if name not in cols:
            kw = {"nullable": nullable}
            if default is not None:
                kw["server_default"] = default
            op.add_column("verifications", sa.Column(name, col_type, **kw))


def downgrade() -> None:
    op.drop_column('verifications', 'voip_rejected')
    op.drop_column('verifications', 'area_code_surcharge')
    op.drop_column('verifications', 'carrier_surcharge')
    op.drop_column('verifications', 'real_carrier')
    op.drop_column('verifications', 'carrier_matched')
    op.drop_column('verifications', 'area_code_matched')
    op.drop_column('verifications', 'retry_attempts')
