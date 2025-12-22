"""add stripe webhook events table

Revision ID: 029_stripe_webhook_events
Revises: 028_production_auth_v1
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '029_stripe_webhook_events'
down_revision = '028_production_auth_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Create stripe_webhook_events table for event deduplication
    op.create_table(
        'stripe_webhook_events',
        sa.Column('event_id', sa.String(), nullable=False, primary_key=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),  # pending, processed, failed
        sa.Column('event_data', sa.Text(), nullable=True),  # Store full event JSON for debugging
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on event_type and status for querying
    op.create_index('ix_stripe_webhook_events_event_type', 'stripe_webhook_events', ['event_type'])
    op.create_index('ix_stripe_webhook_events_status', 'stripe_webhook_events', ['status'])
    op.create_index('ix_stripe_webhook_events_received_at', 'stripe_webhook_events', ['received_at'])


def downgrade():
    op.drop_index('ix_stripe_webhook_events_received_at', table_name='stripe_webhook_events')
    op.drop_index('ix_stripe_webhook_events_status', table_name='stripe_webhook_events')
    op.drop_index('ix_stripe_webhook_events_event_type', table_name='stripe_webhook_events')
    op.drop_table('stripe_webhook_events')

