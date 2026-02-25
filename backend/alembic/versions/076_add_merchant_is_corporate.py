"""Add is_corporate column to merchants table

Revision ID: 076_merchant_is_corporate
Revises: 075_device_tokens
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '076_merchant_is_corporate'
down_revision = None  # Standalone — run after all existing migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_corporate column (default False for existing rows)
    op.add_column(
        'merchants',
        sa.Column('is_corporate', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('idx_merchants_is_corporate', 'merchants', ['is_corporate'])


def downgrade() -> None:
    op.drop_index('idx_merchants_is_corporate', table_name='merchants')
    op.drop_column('merchants', 'is_corporate')
