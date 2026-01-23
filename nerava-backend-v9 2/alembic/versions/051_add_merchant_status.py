"""Add status column to merchants table

Revision ID: 051_merchant_status
Revises: 050_exclusive_caps
Create Date: 2025-01-27 14:10:00.000000

Adds status column to merchants table (default: "active", values: "active", "paused")
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '051_merchant_status'
down_revision = '050_exclusive_caps'
branch_labels = None
depends_on = None


def upgrade():
    """Add status column to merchants table"""
    bind = op.get_bind()
    
    # Check which columns already exist
    from sqlalchemy import inspect
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('merchants')]
    
    # Only add column if it doesn't exist
    if 'status' not in existing_columns:
        op.add_column('merchants', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
        # Add index on status for filtering
        op.create_index('ix_merchants_status', 'merchants', ['status'], unique=False)


def downgrade():
    """Remove status column from merchants table"""
    op.drop_index('ix_merchants_status', table_name='merchants')
    op.drop_column('merchants', 'status')

