"""Add Phase 0 fields to arrival_sessions

Revision ID: 067
Revises: 066
Create Date: 2026-02-09

Adds columns for Phase 0 phone-first EV arrival flow:
- phone_session_token: UUID token stored in localStorage
- car_verified fields: Car verification metadata
- promo_code fields: Promo code generation and tracking
- phase0_state: State machine for Phase 0 flow
"""
from alembic import op
import sqlalchemy as sa

revision = '067'
down_revision = '066'
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

    # Make driver_id nullable for Phase 0 (no auth required)
    # This alter is safe to run multiple times
    op.alter_column('arrival_sessions', 'driver_id', nullable=True)

    # All columns to add with their specs
    columns = [
        ('phone_session_token', sa.String(64), {'nullable': True}),
        ('car_verified_at', sa.DateTime(), {'nullable': True}),
        ('car_user_agent', sa.String(512), {'nullable': True}),
        ('car_ip', sa.String(45), {'nullable': True}),
        ('pin_attempts', sa.Integer(), {'server_default': '0', 'nullable': False}),
        ('promo_code', sa.String(8), {'nullable': True}),
        ('promo_code_expires_at', sa.DateTime(), {'nullable': True}),
        ('promo_code_revealed_at', sa.DateTime(), {'nullable': True}),
        ('promo_code_redeemed_at', sa.DateTime(), {'nullable': True}),
        ('arrived_at', sa.DateTime(), {'nullable': True}),
        ('phase0_state', sa.String(20), {'server_default': 'pending', 'nullable': True}),
    ]

    for col_name, col_type, kwargs in columns:
        if not _column_exists('arrival_sessions', col_name, bind):
            op.add_column('arrival_sessions', sa.Column(col_name, col_type, **kwargs))

    # Indexes (skip if exist)
    if not _index_exists('arrival_sessions', 'ix_arrival_sessions_phone_token', bind):
        op.create_index('ix_arrival_sessions_phone_token', 'arrival_sessions', ['phone_session_token'])
    if not _index_exists('arrival_sessions', 'ix_arrival_sessions_promo_code', bind):
        op.create_index('ix_arrival_sessions_promo_code', 'arrival_sessions', ['promo_code'])
    if not _index_exists('arrival_sessions', 'ix_arrival_sessions_phase0_state', bind):
        op.create_index('ix_arrival_sessions_phase0_state', 'arrival_sessions', ['phase0_state'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_arrival_sessions_phase0_state', table_name='arrival_sessions')
    op.drop_index('ix_arrival_sessions_promo_code', table_name='arrival_sessions')
    op.drop_index('ix_arrival_sessions_phone_token', table_name='arrival_sessions')
    
    # Drop columns
    op.drop_column('arrival_sessions', 'phase0_state')
    
    # Restore driver_id NOT NULL constraint
    op.alter_column('arrival_sessions', 'driver_id', nullable=False)
    op.drop_column('arrival_sessions', 'arrived_at')
    op.drop_column('arrival_sessions', 'promo_code_redeemed_at')
    op.drop_column('arrival_sessions', 'promo_code_revealed_at')
    op.drop_column('arrival_sessions', 'promo_code_expires_at')
    op.drop_column('arrival_sessions', 'promo_code')
    op.drop_column('arrival_sessions', 'pin_attempts')
    op.drop_column('arrival_sessions', 'car_ip')
    op.drop_column('arrival_sessions', 'car_user_agent')
    op.drop_column('arrival_sessions', 'car_verified_at')
    op.drop_column('arrival_sessions', 'phone_session_token')
