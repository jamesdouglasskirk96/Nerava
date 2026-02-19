"""Add EV Arrival Code fields to arrival_sessions

Revision ID: 066
Revises: 065
Create Date: 2026-02-07

Adds columns for the V0 EV Arrival Code flow:
- flow_type: 'legacy' or 'arrival_code'
- arrival_code: unique code like NVR-4821
- verification and pairing fields
"""
from alembic import op
import sqlalchemy as sa

revision = '066'
down_revision = '065'
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
        ('flow_type', sa.String(20), {'nullable': False, 'server_default': 'legacy'}),
        ('arrival_code', sa.String(10), {'nullable': True}),
        ('arrival_code_generated_at', sa.DateTime(), {'nullable': True}),
        ('arrival_code_expires_at', sa.DateTime(), {'nullable': True}),
        ('arrival_code_redeemed_at', sa.DateTime(), {'nullable': True}),
        ('arrival_code_redemption_count', sa.Integer(), {'nullable': False, 'server_default': '0'}),
        ('verification_method', sa.String(20), {'nullable': True}),
        ('verified_at', sa.DateTime(), {'nullable': True}),
        ('verification_attempts', sa.Integer(), {'nullable': False, 'server_default': '0'}),
        ('checkout_url_sent', sa.String(500), {'nullable': True}),
        ('sms_sent_at', sa.DateTime(), {'nullable': True}),
        ('sms_message_sid', sa.String(50), {'nullable': True}),
        ('pairing_token', sa.String(64), {'nullable': True}),
        ('pairing_token_expires_at', sa.DateTime(), {'nullable': True}),
        ('paired_at', sa.DateTime(), {'nullable': True}),
        ('paired_phone', sa.String(20), {'nullable': True}),
    ]

    for col_name, col_type, kwargs in columns:
        if not _column_exists('arrival_sessions', col_name, bind):
            op.add_column('arrival_sessions', sa.Column(col_name, col_type, **kwargs))

    # Create indexes (skip if exist)
    if not _index_exists('arrival_sessions', 'idx_arrival_code_unique', bind):
        op.create_index('idx_arrival_code_unique', 'arrival_sessions', ['arrival_code'], unique=True)
    if not _index_exists('arrival_sessions', 'idx_pairing_token_unique', bind):
        op.create_index('idx_pairing_token_unique', 'arrival_sessions', ['pairing_token'], unique=True)
    if not _index_exists('arrival_sessions', 'idx_flow_type', bind):
        op.create_index('idx_flow_type', 'arrival_sessions', ['flow_type'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_flow_type', table_name='arrival_sessions')
    op.drop_index('idx_pairing_token_unique', table_name='arrival_sessions')
    op.drop_index('idx_arrival_code_unique', table_name='arrival_sessions')

    # Drop columns in reverse order
    op.drop_column('arrival_sessions', 'paired_phone')
    op.drop_column('arrival_sessions', 'paired_at')
    op.drop_column('arrival_sessions', 'pairing_token_expires_at')
    op.drop_column('arrival_sessions', 'pairing_token')
    op.drop_column('arrival_sessions', 'sms_message_sid')
    op.drop_column('arrival_sessions', 'sms_sent_at')
    op.drop_column('arrival_sessions', 'checkout_url_sent')
    op.drop_column('arrival_sessions', 'verification_attempts')
    op.drop_column('arrival_sessions', 'verified_at')
    op.drop_column('arrival_sessions', 'verification_method')
    op.drop_column('arrival_sessions', 'arrival_code_redemption_count')
    op.drop_column('arrival_sessions', 'arrival_code_redeemed_at')
    op.drop_column('arrival_sessions', 'arrival_code_expires_at')
    op.drop_column('arrival_sessions', 'arrival_code_generated_at')
    op.drop_column('arrival_sessions', 'arrival_code')
    op.drop_column('arrival_sessions', 'flow_type')
