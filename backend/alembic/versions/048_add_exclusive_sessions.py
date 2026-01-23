"""add exclusive sessions

Revision ID: 048_add_exclusive_sessions
Revises: 047_add_wallet_pass_states
Create Date: 2025-01-27 12:00:00.000000

Adds exclusive session model for web-only driver flow
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '048_add_exclusive_sessions'
down_revision = '047_add_wallet_pass_states'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create exclusive_sessions table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # UUID type handling
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.UUID()
    
    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()
    
    # ExclusiveSession table
    op.create_table(
        'exclusive_sessions',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=True),
        sa.Column('merchant_place_id', sa.String(), nullable=True),
        sa.Column('charger_id', sa.String(), nullable=True),
        sa.Column('charger_place_id', sa.String(), nullable=True),
        sa.Column('intent_session_id', uuid_type, nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('activated_at', datetime_type, nullable=False),
        sa.Column('expires_at', datetime_type, nullable=False),
        sa.Column('completed_at', datetime_type, nullable=True),
        sa.Column('created_at', datetime_type, nullable=False),
        sa.Column('updated_at', datetime_type, nullable=False),
        sa.Column('activation_lat', sa.Float(), nullable=True),
        sa.Column('activation_lng', sa.Float(), nullable=True),
        sa.Column('activation_accuracy_m', sa.Float(), nullable=True),
        sa.Column('activation_distance_to_charger_m', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ),
        sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ),
        sa.ForeignKeyConstraint(['intent_session_id'], ['intent_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('ix_exclusive_sessions_driver_id', 'exclusive_sessions', ['driver_id'])
    op.create_index('ix_exclusive_sessions_status', 'exclusive_sessions', ['status'])
    op.create_index('ix_exclusive_sessions_merchant_id', 'exclusive_sessions', ['merchant_id'])
    op.create_index('ix_exclusive_sessions_merchant_place_id', 'exclusive_sessions', ['merchant_place_id'])
    op.create_index('ix_exclusive_sessions_charger_id', 'exclusive_sessions', ['charger_id'])
    op.create_index('ix_exclusive_sessions_intent_session_id', 'exclusive_sessions', ['intent_session_id'])
    op.create_index('ix_exclusive_sessions_expires_at', 'exclusive_sessions', ['expires_at'])
    op.create_index('idx_exclusive_sessions_driver_status', 'exclusive_sessions', ['driver_id', 'status'])
    op.create_index('idx_exclusive_sessions_expires_at', 'exclusive_sessions', ['expires_at'])


def downgrade() -> None:
    """Drop exclusive_sessions table"""
    op.drop_index('idx_exclusive_sessions_expires_at', table_name='exclusive_sessions')
    op.drop_index('idx_exclusive_sessions_driver_status', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_expires_at', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_intent_session_id', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_charger_id', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_merchant_place_id', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_merchant_id', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_status', table_name='exclusive_sessions')
    op.drop_index('ix_exclusive_sessions_driver_id', table_name='exclusive_sessions')
    op.drop_table('exclusive_sessions')

