"""add transaction ids to purchase outcomes

Revision ID: d6e7f8g9h0i1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6e7f8g9h0i1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add debit_transaction_id column (String to match balance_transactions.id)
    op.add_column('purchase_outcomes', 
        sa.Column('debit_transaction_id', sa.String(), nullable=True)
    )
    
    # Add refund_transaction_id column (String to match balance_transactions.id)
    op.add_column('purchase_outcomes',
        sa.Column('refund_transaction_id', sa.String(), nullable=True)
    )
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_purchase_outcomes_debit_transaction',
        'purchase_outcomes', 'balance_transactions',
        ['debit_transaction_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_purchase_outcomes_refund_transaction',
        'purchase_outcomes', 'balance_transactions',
        ['refund_transaction_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_purchase_outcomes_refund_transaction', 'purchase_outcomes', type_='foreignkey')
    op.drop_constraint('fk_purchase_outcomes_debit_transaction', 'purchase_outcomes', type_='foreignkey')
    
    # Drop columns
    op.drop_column('purchase_outcomes', 'refund_transaction_id')
    op.drop_column('purchase_outcomes', 'debit_transaction_id')
