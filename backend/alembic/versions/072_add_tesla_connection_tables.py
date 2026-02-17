"""Add Tesla connection and EV verification code tables

Revision ID: 072
Revises: 071_fix_arrival_sessions_id_type
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '072'
down_revision = '071_fix_arrival_sessions_id_type'
branch_labels = None
depends_on = None


def upgrade():
    # Create tesla_connections table
    op.create_table(
        'tesla_connections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(), nullable=False),
        sa.Column('tesla_user_id', sa.String(100), nullable=True),
        sa.Column('vehicle_id', sa.String(100), nullable=True),
        sa.Column('vin', sa.String(17), nullable=True),
        sa.Column('vehicle_name', sa.String(100), nullable=True),
        sa.Column('vehicle_model', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_tesla_connection_user', 'tesla_connections', ['user_id'])
    op.create_index('idx_tesla_connection_vehicle', 'tesla_connections', ['vehicle_id'])

    # Create ev_verification_codes table
    op.create_table(
        'ev_verification_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tesla_connection_id', sa.String(36), sa.ForeignKey('tesla_connections.id'), nullable=True),
        sa.Column('code', sa.String(10), unique=True, nullable=False),
        sa.Column('charger_id', sa.String(100), nullable=True),
        sa.Column('merchant_place_id', sa.String(255), nullable=True),
        sa.Column('merchant_name', sa.String(255), nullable=True),
        sa.Column('charging_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('charge_rate_kw', sa.Integer(), nullable=True),
        sa.Column('lat', sa.String(20), nullable=True),
        sa.Column('lng', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('redeemed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_ev_code', 'ev_verification_codes', ['code'])
    op.create_index('idx_ev_code_user_status', 'ev_verification_codes', ['user_id', 'status'])


def downgrade():
    op.drop_table('ev_verification_codes')
    op.drop_table('tesla_connections')
