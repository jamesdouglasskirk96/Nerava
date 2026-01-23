"""add outbox retry fields

Revision ID: 050_add_outbox_retry_fields
Revises: 049_add_primary_merchant_override
Create Date: 2025-01-27 12:00:00.000000

Adds attempt_count and last_error columns to outbox_events table for retry logic.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '050_add_outbox_retry_fields'
down_revision = '049_add_primary_merchant_override'
branch_labels = None
depends_on = None


def _table_exists(table_name: str, inspector) -> bool:
    """Check if a table exists"""
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str, inspector) -> bool:
    """Check if a column exists in a table"""
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    """Add retry fields to outbox_events table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Only add columns if table exists
    if _table_exists('outbox_events', inspector):
        if not _column_exists('outbox_events', 'attempt_count', inspector):
            op.add_column('outbox_events', sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'))
        if not _column_exists('outbox_events', 'last_error', inspector):
            op.add_column('outbox_events', sa.Column('last_error', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove retry fields from outbox_events table"""
    op.drop_column('outbox_events', 'last_error')
    op.drop_column('outbox_events', 'attempt_count')


