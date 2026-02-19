"""Add virtual_keys table for Tesla Virtual Key onboarding

Revision ID: 065
Revises: 064
Create Date: 2026-02-06

Creates virtual_keys table for storing Tesla vehicle pairing information.
Enables automatic arrival detection via Tesla Fleet Telemetry.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '065'
down_revision = '064'
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


def upgrade():
    bind = op.get_bind()

    # Skip if table already exists
    if _table_exists('virtual_keys', bind):
        return

    # Create virtual_keys table (use String(36) instead of UUID for compatibility)
    op.create_table(
        'virtual_keys',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tesla_vehicle_id', sa.String(100), nullable=True),
        sa.Column('vin', sa.String(17), nullable=True),
        sa.Column('vehicle_name', sa.String(100), nullable=True),
        sa.Column('provisioning_token', sa.String(255), nullable=False),
        sa.Column('qr_code_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('paired_at', sa.DateTime(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('pairing_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_telemetry_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # Create indexes (skip if exist)
    if not _index_exists('virtual_keys', 'idx_virtual_key_user_status', bind):
        op.create_index('idx_virtual_key_user_status', 'virtual_keys', ['user_id', 'status'])
    if not _index_exists('virtual_keys', 'idx_virtual_key_provisioning_token', bind):
        op.create_index('idx_virtual_key_provisioning_token', 'virtual_keys', ['provisioning_token'], unique=True)


def downgrade():
    op.drop_index('idx_virtual_key_provisioning_token', table_name='virtual_keys')
    op.drop_index('idx_virtual_key_user_status', table_name='virtual_keys')
    op.drop_table('virtual_keys')
