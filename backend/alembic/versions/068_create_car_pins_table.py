"""Create car_pins table

Revision ID: 068
Revises: 067
Create Date: 2026-02-09

Creates car_pins table for Phase 0 PIN pairing.
PINs are stored separately because the car browser doesn't know about any phone session.
The PIN acts as a linking token.
"""
from alembic import op
import sqlalchemy as sa

revision = '068'
down_revision = '067'
branch_labels = None
depends_on = None


def _table_exists(table_name: str, bind) -> bool:
    from sqlalchemy import inspect
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade():
    bind = op.get_bind()

    # Skip if table already exists
    if _table_exists('car_pins', bind):
        return

    # Use String(36) for id to match arrival_sessions.id type
    op.create_table(
        'car_pins',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('pin', sa.String(7), nullable=False, unique=True),  # Format: XXX-XXX
        sa.Column('user_agent', sa.String(512), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),  # NULL = not used yet
        sa.Column('used_by_session_id', sa.String(36), sa.ForeignKey('arrival_sessions.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes (skip if exist)
    if not _index_exists('car_pins', 'ix_car_pins_pin', bind):
        op.create_index('ix_car_pins_pin', 'car_pins', ['pin'])
    if not _index_exists('car_pins', 'ix_car_pins_expires_at', bind):
        op.create_index('ix_car_pins_expires_at', 'car_pins', ['expires_at'])


def downgrade():
    op.drop_index('ix_car_pins_expires_at', table_name='car_pins')
    op.drop_index('ix_car_pins_pin', table_name='car_pins')
    op.drop_table('car_pins')
