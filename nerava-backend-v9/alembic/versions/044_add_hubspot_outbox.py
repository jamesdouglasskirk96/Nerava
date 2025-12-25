"""add hubspot outbox

Revision ID: 044_add_hubspot_outbox
Revises: 043_add_admin_audit_log
Create Date: 2025-01-31 12:00:00.000000

P3: Adds hubspot_outbox table for dry-run mode and event replay.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '044_add_hubspot_outbox'
down_revision = '043_add_admin_audit_log'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create hubspot_outbox table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Use JSON for PostgreSQL, TEXT for SQLite
    json_type = sa.JSON() if dialect_name != 'sqlite' else sa.Text()
    
    op.create_table(
        'hubspot_outbox',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload_json', json_type, nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_hubspot_outbox_event_type', 'hubspot_outbox', ['event_type'])
    op.create_index('ix_hubspot_outbox_created_at', 'hubspot_outbox', ['created_at'])
    op.create_index('ix_hubspot_outbox_sent_at', 'hubspot_outbox', ['sent_at'])
    op.create_index('ix_hubspot_outbox_event_created', 'hubspot_outbox', ['event_type', 'created_at'])
    op.create_index('ix_hubspot_outbox_sent_created', 'hubspot_outbox', ['sent_at', 'created_at'])


def downgrade() -> None:
    """Drop hubspot_outbox table"""
    op.drop_index('ix_hubspot_outbox_sent_created', table_name='hubspot_outbox')
    op.drop_index('ix_hubspot_outbox_event_created', table_name='hubspot_outbox')
    op.drop_index('ix_hubspot_outbox_sent_at', table_name='hubspot_outbox')
    op.drop_index('ix_hubspot_outbox_created_at', table_name='hubspot_outbox')
    op.drop_index('ix_hubspot_outbox_event_type', table_name='hubspot_outbox')
    op.drop_table('hubspot_outbox')

