"""logic v1

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to merchant_intel_forecasts
    op.add_column('merchant_intel_forecasts', sa.Column('version', sa.String(10), nullable=False, server_default='v1'))
    op.add_column('merchant_intel_forecasts', sa.Column('inputs', sa.JSON(), nullable=True))
    
    # Add columns to utility_behavior_snapshots  
    op.add_column('utility_behavior_snapshots', sa.Column('version', sa.String(10), nullable=False, server_default='v1'))
    op.add_column('utility_behavior_snapshots', sa.Column('inputs', sa.JSON(), nullable=True))
    
    # Create energy_rep_backfills table
    op.create_table('energy_rep_backfills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'day', name='uq_energy_rep_backfill_user_day')
    )


def downgrade():
    op.drop_table('energy_rep_backfills')
    op.drop_column('utility_behavior_snapshots', 'inputs')
    op.drop_column('utility_behavior_snapshots', 'version')
    op.drop_column('merchant_intel_forecasts', 'inputs')
    op.drop_column('merchant_intel_forecasts', 'version')
