"""Add is_corporate column to merchants table

Revision ID: 076_merchant_is_corporate
Revises: 075_device_tokens
Create Date: 2026-02-24
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

# revision identifiers
revision = '076_merchant_is_corporate'
down_revision = '075_device_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    # Add is_corporate column (default False for existing rows)
    existing_columns = [c['name'] for c in inspector.get_columns('merchants')] if 'merchants' in existing_tables else []
    if 'is_corporate' not in existing_columns:
        op.add_column(
            'merchants',
            sa.Column('is_corporate', sa.Boolean(), nullable=False, server_default='false'),
        )
    try:
        op.create_index('idx_merchants_is_corporate', 'merchants', ['is_corporate'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('idx_merchants_is_corporate', table_name='merchants')
    op.drop_column('merchants', 'is_corporate')
