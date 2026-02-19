"""Add missing fields to arrival_sessions

Revision ID: 070
Revises: 069
Create Date: 2026-02-10

Adds columns that exist in the ArrivalSession model but were never added to DB:
- browser_source, ev_brand, ev_firmware
- fulfillment_type, queued_order_status
- destination fields
- arrival detection timestamps
- virtual_key integration fields
"""
from alembic import op
import sqlalchemy as sa

revision = '070'
down_revision = '069'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, bind) -> bool:
    from sqlalchemy import inspect
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade():
    bind = op.get_bind()

    # All columns to add with their specs
    columns = [
        # Browser detection fields
        ('browser_source', sa.String(30), {'nullable': True}),
        ('ev_brand', sa.String(30), {'nullable': True}),
        ('ev_firmware', sa.String(50), {'nullable': True}),

        # Fulfillment type
        ('fulfillment_type', sa.String(20), {'nullable': True}),

        # Order queuing
        ('queued_order_status', sa.String(20), {'nullable': True, 'server_default': 'queued'}),

        # Destination fields
        ('destination_merchant_id', sa.String(255), {'nullable': True}),
        ('destination_lat', sa.Float(), {'nullable': True}),
        ('destination_lng', sa.Float(), {'nullable': True}),

        # Arrival detection timestamps
        ('arrival_detected_at', sa.DateTime(), {'nullable': True}),
        ('order_released_at', sa.DateTime(), {'nullable': True}),
        ('order_ready_at', sa.DateTime(), {'nullable': True}),

        # Distance when arrival was detected
        ('arrival_distance_m', sa.Float(), {'nullable': True}),

        # Virtual Key integration
        ('virtual_key_id', sa.String(36), {'nullable': True}),
        ('arrival_source', sa.String(30), {'nullable': True}),
        ('vehicle_soc_at_arrival', sa.Float(), {'nullable': True}),
    ]

    for col_name, col_type, kwargs in columns:
        if not _column_exists('arrival_sessions', col_name, bind):
            op.add_column('arrival_sessions', sa.Column(col_name, col_type, **kwargs))

    # Add indexes if they don't exist
    if not _index_exists('arrival_sessions', 'idx_arrival_queued', bind):
        op.create_index('idx_arrival_queued', 'arrival_sessions', ['queued_order_status', 'destination_merchant_id'])


def downgrade():
    # Drop index
    op.drop_index('idx_arrival_queued', table_name='arrival_sessions')

    # Drop columns in reverse order
    op.drop_column('arrival_sessions', 'vehicle_soc_at_arrival')
    op.drop_column('arrival_sessions', 'arrival_source')
    op.drop_column('arrival_sessions', 'virtual_key_id')
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
