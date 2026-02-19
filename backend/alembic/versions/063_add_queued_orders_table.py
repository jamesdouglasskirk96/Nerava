"""Add queued_orders table for arrival-triggered order release

Revision ID: 063
Revises: 062
Create Date: 2026-02-06

This table stores driver order intents that are held until arrival is confirmed.
The order is NOT sent to the merchant until the queued_order status = RELEASED.

Status flow:
  QUEUED → RELEASED (on arrival confirmation)
  QUEUED → CANCELED (if session canceled)
  QUEUED → EXPIRED (if session expires)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '063'
down_revision = '062'
branch_labels = None
depends_on = None


def _table_exists(table_name: str, bind) -> bool:
    """Check if a table exists"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    """Check if an index exists on a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()

    # Skip if table already exists
    if _table_exists('queued_orders', bind):
        return

    # Create queued_orders table
    # Note: Use String(36) for IDs to match arrival_sessions.id type
    op.create_table(
        'queued_orders',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('arrival_session_id', sa.String(36), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),
        sa.Column('ordering_url', sa.Text(), nullable=False),
        sa.Column('release_url', sa.Text(), nullable=True),
        sa.Column('order_number', sa.String(100), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['arrival_session_id'], ['arrival_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.UniqueConstraint('arrival_session_id', name='uq_queued_order_session'),
    )

    # Create indexes (skip if exist)
    if not _index_exists('queued_orders', 'idx_queued_order_session', bind):
        op.create_index('idx_queued_order_session', 'queued_orders', ['arrival_session_id'], unique=True)
    if not _index_exists('queued_orders', 'idx_queued_order_merchant_status', bind):
        op.create_index('idx_queued_order_merchant_status', 'queued_orders', ['merchant_id', 'status'])
    if not _index_exists('queued_orders', 'idx_queued_order_created', bind):
        op.create_index('idx_queued_order_created', 'queued_orders', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_queued_order_created', table_name='queued_orders')
    op.drop_index('idx_queued_order_merchant_status', table_name='queued_orders')
    op.drop_index('idx_queued_order_session', table_name='queued_orders')
    op.drop_table('queued_orders')
