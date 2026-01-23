"""Add vehicle tables for Smartcar integration

Revision ID: 020
Revises: 019
Create Date: 2025-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    # 1. Create vehicle_accounts table
    if not _has_table('vehicle_accounts'):
        op.create_table(
            'vehicle_accounts',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('provider', sa.String(), nullable=False),
            sa.Column('provider_vehicle_id', sa.String(), nullable=False),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_vehicle_accounts_user_id', 'vehicle_accounts', ['user_id'])
        op.create_index('ix_vehicle_accounts_provider', 'vehicle_accounts', ['provider'])
    
    # 2. Create vehicle_tokens table
    if not _has_table('vehicle_tokens'):
        op.create_table(
            'vehicle_tokens',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('vehicle_account_id', sa.String(), sa.ForeignKey('vehicle_accounts.id'), nullable=False),
            sa.Column('access_token', sa.String(), nullable=False),
            sa.Column('refresh_token', sa.String(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('scope', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_vehicle_tokens_vehicle_account_id', 'vehicle_tokens', ['vehicle_account_id'])
    
    # 3. Create vehicle_telemetry table
    if not _has_table('vehicle_telemetry'):
        # Use JSON for Postgres, TEXT for SQLite
        json_type = sa.JSON() if op.get_bind().dialect.name != 'sqlite' else sa.Text()
        
        op.create_table(
            'vehicle_telemetry',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('vehicle_account_id', sa.String(), sa.ForeignKey('vehicle_accounts.id'), nullable=False),
            sa.Column('recorded_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('soc_pct', sa.Float(), nullable=True),
            sa.Column('charging_state', sa.String(), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('raw_json', json_type, nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_vehicle_telemetry_vehicle_account_id', 'vehicle_telemetry', ['vehicle_account_id'])
        op.create_index('ix_vehicle_telemetry_recorded_at', 'vehicle_telemetry', ['recorded_at'])


def downgrade() -> None:
    if _has_table('vehicle_telemetry'):
        op.drop_index('ix_vehicle_telemetry_recorded_at', table_name='vehicle_telemetry', if_exists=True)
        op.drop_index('ix_vehicle_telemetry_vehicle_account_id', table_name='vehicle_telemetry', if_exists=True)
        op.drop_table('vehicle_telemetry')
    
    if _has_table('vehicle_tokens'):
        op.drop_index('ix_vehicle_tokens_vehicle_account_id', table_name='vehicle_tokens', if_exists=True)
        op.drop_table('vehicle_tokens')
    
    if _has_table('vehicle_accounts'):
        op.drop_index('ix_vehicle_accounts_provider', table_name='vehicle_accounts', if_exists=True)
        op.drop_index('ix_vehicle_accounts_user_id', table_name='vehicle_accounts', if_exists=True)
        op.drop_table('vehicle_accounts')

