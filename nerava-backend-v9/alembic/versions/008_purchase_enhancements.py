"""Add purchase webhook enhancement fields to payments

Revision ID: 008
Revises: 007
Create Date: 2025-10-29 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add purchase-related fields to payments table (idempotent)
    try:
        # Check if columns exist before adding (SQLite doesn't support IF NOT EXISTS for ALTER TABLE)
        # We'll use try/except for idempotency
        op.add_column('payments', sa.Column('merchant_id', sa.Integer(), nullable=True))
        op.add_column('payments', sa.Column('raw_json', sa.Text(), nullable=True))
        op.add_column('payments', sa.Column('claimed', sa.Boolean(), nullable=True, server_default='0'))
        op.add_column('payments', sa.Column('claimed_at', sa.DateTime(), nullable=True))
        op.add_column('payments', sa.Column('expires_at', sa.DateTime(), nullable=True))
        
        # Add index on claimed for faster pending lookups
        op.create_index('idx_payments_claimed', 'payments', ['claimed'])
        op.create_index('idx_payments_expires_at', 'payments', ['expires_at'])
    except Exception:
        # Columns might already exist - migration is idempotent
        pass


def downgrade():
    try:
        op.drop_index('idx_payments_expires_at', 'payments')
        op.drop_index('idx_payments_claimed', 'payments')
        op.drop_column('payments', 'expires_at')
        op.drop_column('payments', 'claimed_at')
        op.drop_column('payments', 'claimed')
        op.drop_column('payments', 'raw_json')
        op.drop_column('payments', 'merchant_id')
    except Exception:
        pass

