"""Add analytics events table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Create analytics_events table
    op.create_table('analytics_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('aggregate_id', sa.String(100), nullable=False),
        sa.Column('properties', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for performance
    op.create_index('idx_analytics_events_type', 'analytics_events', ['event_type'])
    op.create_index('idx_analytics_events_timestamp', 'analytics_events', ['timestamp'])
    op.create_index('idx_analytics_events_region', 'analytics_events', ['region'])
    op.create_index('idx_analytics_events_aggregate', 'analytics_events', ['aggregate_id'])

def downgrade():
    op.drop_index('idx_analytics_events_aggregate', 'analytics_events')
    op.drop_index('idx_analytics_events_region', 'analytics_events')
    op.drop_index('idx_analytics_events_timestamp', 'analytics_events')
    op.drop_index('idx_analytics_events_type', 'analytics_events')
    op.drop_table('analytics_events')
