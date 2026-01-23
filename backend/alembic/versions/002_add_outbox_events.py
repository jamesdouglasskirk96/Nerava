"""Add outbox events table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create outbox_events table
    op.create_table('outbox_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for performance
    op.create_index('idx_outbox_events_processed', 'outbox_events', ['processed_at'])
    op.create_index('idx_outbox_events_type', 'outbox_events', ['event_type'])
    op.create_index('idx_outbox_events_created', 'outbox_events', ['created_at'])

def downgrade():
    op.drop_index('idx_outbox_events_created', 'outbox_events')
    op.drop_index('idx_outbox_events_type', 'outbox_events')
    op.drop_index('idx_outbox_events_processed', 'outbox_events')
    op.drop_table('outbox_events')
