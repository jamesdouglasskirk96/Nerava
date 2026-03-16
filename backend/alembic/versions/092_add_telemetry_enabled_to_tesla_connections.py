"""Add telemetry_enabled and telemetry_configured_at to tesla_connections

Revision ID: 092_add_telemetry_enabled_to_tesla_connections
Revises: 091_add_num_evse_to_chargers
Create Date: 2026-03-02

Supports Tesla Fleet Telemetry integration for real-time charging detection.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '092_add_telemetry_enabled_to_tesla_connections'
down_revision = '091_add_num_evse_to_chargers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tesla_connections',
        sa.Column('telemetry_enabled', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.add_column(
        'tesla_connections',
        sa.Column('telemetry_configured_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('tesla_connections', 'telemetry_configured_at')
    op.drop_column('tesla_connections', 'telemetry_enabled')
