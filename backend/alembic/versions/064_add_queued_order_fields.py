"""Add queued order fields to arrival_sessions

Revision ID: 064
Revises: 063
Create Date: 2026-02-06

Adds fields for Tesla browser detection and order queuing:
- Browser detection (browser_source, ev_brand, ev_firmware)
- Fulfillment type (ev_dine_in, ev_curbside)
- Order queuing status (queued_order_status)
- Destination tracking (destination_merchant_id, destination_lat/lng)
- Arrival timestamps (arrival_detected_at, order_released_at, order_ready_at)
- Arrival distance (arrival_distance_m)
"""
from alembic import op
import sqlalchemy as sa

revision = '064'
down_revision = '063'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, bind) -> bool:
    """Check if a column exists in a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    """Check if an index exists on a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _constraint_exists(table_name: str, constraint_name: str, bind) -> bool:
    """Check if a foreign key constraint exists"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    fks = inspector.get_foreign_keys(table_name)
    return any(fk.get("name") == constraint_name for fk in fks)


def upgrade():
    bind = op.get_bind()

    # Browser detection (skip if exist)
    if not _column_exists('arrival_sessions', 'browser_source', bind):
        op.add_column('arrival_sessions',
            sa.Column('browser_source', sa.String(30), nullable=True))
    if not _column_exists('arrival_sessions', 'ev_brand', bind):
        op.add_column('arrival_sessions',
            sa.Column('ev_brand', sa.String(30), nullable=True))
    if not _column_exists('arrival_sessions', 'ev_firmware', bind):
        op.add_column('arrival_sessions',
            sa.Column('ev_firmware', sa.String(50), nullable=True))

    # Fulfillment
    if not _column_exists('arrival_sessions', 'fulfillment_type', bind):
        op.add_column('arrival_sessions',
            sa.Column('fulfillment_type', sa.String(20), nullable=True))

    # Order queuing
    if not _column_exists('arrival_sessions', 'queued_order_status', bind):
        op.add_column('arrival_sessions',
            sa.Column('queued_order_status', sa.String(20), nullable=True))

    # Destination for arrival detection
    if not _column_exists('arrival_sessions', 'destination_merchant_id', bind):
        op.add_column('arrival_sessions',
            sa.Column('destination_merchant_id', sa.String(), nullable=True))
    if not _column_exists('arrival_sessions', 'destination_lat', bind):
        op.add_column('arrival_sessions',
            sa.Column('destination_lat', sa.Float(), nullable=True))
    if not _column_exists('arrival_sessions', 'destination_lng', bind):
        op.add_column('arrival_sessions',
            sa.Column('destination_lng', sa.Float(), nullable=True))

    # Timestamps
    if not _column_exists('arrival_sessions', 'arrival_detected_at', bind):
        op.add_column('arrival_sessions',
            sa.Column('arrival_detected_at', sa.DateTime(), nullable=True))
    if not _column_exists('arrival_sessions', 'order_released_at', bind):
        op.add_column('arrival_sessions',
            sa.Column('order_released_at', sa.DateTime(), nullable=True))
    if not _column_exists('arrival_sessions', 'order_ready_at', bind):
        op.add_column('arrival_sessions',
            sa.Column('order_ready_at', sa.DateTime(), nullable=True))

    # Distance
    if not _column_exists('arrival_sessions', 'arrival_distance_m', bind):
        op.add_column('arrival_sessions',
            sa.Column('arrival_distance_m', sa.Float(), nullable=True))

    # Index for finding queued orders (skip if exists)
    if not _index_exists('arrival_sessions', 'idx_arrival_queued', bind):
        op.create_index(
            'idx_arrival_queued',
            'arrival_sessions',
            ['queued_order_status', 'destination_merchant_id'],
        )

    # Add foreign key constraint for destination_merchant_id (skip if exists)
    if not _constraint_exists('arrival_sessions', 'fk_arrival_destination_merchant', bind):
        try:
            op.create_foreign_key(
                'fk_arrival_destination_merchant',
                'arrival_sessions',
                'merchants',
                ['destination_merchant_id'],
                ['id'],
            )
        except Exception:
            pass  # Constraint may already exist under a different name


def downgrade():
    op.drop_constraint('fk_arrival_destination_merchant', 'arrival_sessions', type_='foreignkey')
    op.drop_index('idx_arrival_queued', table_name='arrival_sessions')
    op.drop_column('arrival_sessions', 'arrival_distance_m')
    op.drop_column('arrival_sessions', 'order_ready_at')
    op.drop_column('arrival_sessions', 'order_released_at')
    op.drop_column('arrival_sessions', 'arrival_detected_at')
    op.drop_column('arrival_sessions', 'destination_lng')
    op.drop_column('arrival_sessions', 'destination_lat')
    op.drop_column('arrival_sessions', 'destination_merchant_id')
    op.drop_column('arrival_sessions', 'queued_order_status')
    op.drop_column('arrival_sessions', 'fulfillment_type')
    op.drop_column('arrival_sessions', 'ev_firmware')
    op.drop_column('arrival_sessions', 'ev_brand')
    op.drop_column('arrival_sessions', 'browser_source')
