"""Square order lookup and fee ledger

Revision ID: 027_square_order_lookup_and_fee_ledger
Revises: 026_add_merchant_rewards
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '027_square_order_lookup_and_fee_ledger'
down_revision = '026_add_merchant_rewards'
branch_labels = None
depends_on = None


def upgrade():
    # Add square_order_id to merchant_redemptions
    try:
        op.add_column('merchant_redemptions', sa.Column('square_order_id', sa.String(), nullable=True))
        # Create unique index on (merchant_id, square_order_id)
        # Note: SQLite doesn't support partial unique indexes, so we enforce uniqueness at application level
        # PostgreSQL would use: postgresql_where=sa.text('square_order_id IS NOT NULL')
        op.create_index(
            'ix_merchant_redemptions_merchant_square_order',
            'merchant_redemptions',
            ['merchant_id', 'square_order_id'],
            unique=True
        )
    except Exception:
        # Column might already exist - skip
        pass
    
    # Create merchant_fee_ledger table
    op.create_table(
        'merchant_fee_ledger',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('nova_redeemed_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fee_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(), nullable=False, server_default='accruing'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['domain_merchants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id', 'period_start', name='uq_merchant_fee_ledger_merchant_period')
    )
    
    # Create indexes
    op.create_index('ix_merchant_fee_ledger_merchant_id', 'merchant_fee_ledger', ['merchant_id'])
    op.create_index('ix_merchant_fee_ledger_period_start', 'merchant_fee_ledger', ['period_start'])


def downgrade():
    # Drop indexes
    try:
        op.drop_index('ix_merchant_fee_ledger_period_start', table_name='merchant_fee_ledger')
        op.drop_index('ix_merchant_fee_ledger_merchant_id', table_name='merchant_fee_ledger')
    except Exception:
        pass
    
    # Drop merchant_fee_ledger table
    op.drop_table('merchant_fee_ledger')
    
    # Remove square_order_id from merchant_redemptions
    try:
        op.drop_index('ix_merchant_redemptions_merchant_square_order', table_name='merchant_redemptions')
        op.drop_column('merchant_redemptions', 'square_order_id')
    except Exception:
        pass

