"""add admin audit log

Revision ID: 043_add_admin_audit_log
Revises: 042_add_notification_prefs
Create Date: 2025-01-31 12:00:00.000000

P1-1: Adds admin_audit_logs table to track all wallet mutations and admin actions.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '043_add_admin_audit_log'
down_revision = '042_add_notification_prefs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin_audit_logs table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Use JSON for PostgreSQL, TEXT for SQLite
    json_type = sa.JSON() if dialect_name != 'sqlite' else sa.Text()
    
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('before_json', json_type, nullable=True),
        sa.Column('after_json', json_type, nullable=True),
        sa.Column('metadata_json', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_admin_audit_logs_actor_id', 'admin_audit_logs', ['actor_id'])
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'])
    op.create_index('ix_admin_audit_logs_target_id', 'admin_audit_logs', ['target_id'])
    op.create_index('ix_admin_audit_logs_created_at', 'admin_audit_logs', ['created_at'])
    op.create_index('ix_admin_audit_logs_actor_created', 'admin_audit_logs', ['actor_id', 'created_at'])
    op.create_index('ix_admin_audit_logs_target_created', 'admin_audit_logs', ['target_type', 'target_id', 'created_at'])
    op.create_index('ix_admin_audit_logs_action_created', 'admin_audit_logs', ['action', 'created_at'])


def downgrade() -> None:
    """Drop admin_audit_logs table"""
    op.drop_index('ix_admin_audit_logs_action_created', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_target_created', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_actor_created', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_created_at', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_target_id', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_action', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_actor_id', table_name='admin_audit_logs')
    op.drop_table('admin_audit_logs')

