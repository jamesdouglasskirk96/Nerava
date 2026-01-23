"""Add force close tracking to exclusive sessions

Revision ID: 052_force_close
Revises: 051_merchant_status
Create Date: 2025-01-27 14:20:00.000000

Adds force_close_reason and force_closed_by columns to exclusive_sessions table
Note: FORCE_CLOSED status will be added to the enum in the model file
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '052_force_close'
down_revision = '051_merchant_status'
branch_labels = None
depends_on = None


def upgrade():
    """Add force close fields to exclusive_sessions table"""
    bind = op.get_bind()
    
    # Check which columns already exist
    from sqlalchemy import inspect
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('exclusive_sessions')]
    
    # Only add columns if they don't exist
    if 'force_close_reason' not in existing_columns:
        op.add_column('exclusive_sessions', sa.Column('force_close_reason', sa.Text(), nullable=True))
    if 'force_closed_by' not in existing_columns:
        op.add_column('exclusive_sessions', sa.Column('force_closed_by', sa.Integer(), nullable=True))


def downgrade():
    """Remove force close fields from exclusive_sessions table"""
    op.drop_column('exclusive_sessions', 'force_closed_by')
    op.drop_column('exclusive_sessions', 'force_close_reason')

