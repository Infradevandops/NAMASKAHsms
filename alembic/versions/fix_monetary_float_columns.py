"""Convert monetary Float columns to Numeric(10,4)

Revision ID: fix_monetary_float_columns
Revises: 2bf41b9c69d1
Create Date: 2026-03-20

"""
from alembic import op
import sqlalchemy as sa

revision = "fix_monetary_float_columns"
down_revision = "2bf41b9c69d1"
branch_labels = None
depends_on = None

NUMERIC = sa.Numeric(10, 4)

_user_cols = [
    "credits",
    "free_verifications",
    "bonus_sms_balance",
    "monthly_quota_used",
    "referral_earnings",
]

_subscription_cols = ["price", "discount"]
_referral_cols = ["reward_amount"]


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        for col in _user_cols:
            batch_op.alter_column(col, type_=NUMERIC, existing_type=sa.Float())

    with op.batch_alter_table("subscriptions") as batch_op:
        for col in _subscription_cols:
            batch_op.alter_column(col, type_=NUMERIC, existing_type=sa.Float())

    with op.batch_alter_table("referrals") as batch_op:
        for col in _referral_cols:
            batch_op.alter_column(col, type_=NUMERIC, existing_type=sa.Float())


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        for col in _user_cols:
            batch_op.alter_column(col, type_=sa.Float(), existing_type=NUMERIC)

    with op.batch_alter_table("subscriptions") as batch_op:
        for col in _subscription_cols:
            batch_op.alter_column(col, type_=sa.Float(), existing_type=NUMERIC)

    with op.batch_alter_table("referrals") as batch_op:
        for col in _referral_cols:
            batch_op.alter_column(col, type_=sa.Float(), existing_type=NUMERIC)
