"""add client events table

Revision ID: 039_add_client_events
Revises: 038_merge_heads
Create Date: 2025-01-24 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "039_add_client_events"
down_revision = "038_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'client_events',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event', sa.String(100), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('page', sa.String(200), nullable=True),
        sa.Column('meta', sa.Text(), nullable=True),  # JSON string
        sa.Column('request_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_client_events_user_id', 'client_events', ['user_id'])
    op.create_index('idx_client_events_event', 'client_events', ['event'])
    op.create_index('idx_client_events_ts', 'client_events', ['ts'])
    op.create_index('idx_client_events_request_id', 'client_events', ['request_id'])


def downgrade() -> None:
    op.drop_index('idx_client_events_request_id', 'client_events')
    op.drop_index('idx_client_events_ts', 'client_events')
    op.drop_index('idx_client_events_event', 'client_events')
    op.drop_index('idx_client_events_user_id', 'client_events')
    op.drop_table('client_events')


