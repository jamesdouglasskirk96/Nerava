"""add wallet pass states table

Revision ID: 047_add_wallet_pass_states
Revises: 046_add_merchant_onboarding_tables
Create Date: 2025-12-31 01:00:00.000000

Adds wallet_pass_states table for tracking active wallet passes tied to intent sessions and merchants
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '047_add_wallet_pass_states'
down_revision = '046_add_merchant_onboarding_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create wallet_pass_states table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # UUID type handling
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.UUID()
    
    # WalletPassState table
    op.create_table(
        'wallet_pass_states',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('session_id', uuid_type, nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['intent_sessions.id'], ),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_wallet_pass_states_session_id', 'wallet_pass_states', ['session_id'])
    op.create_index('ix_wallet_pass_states_merchant_id', 'wallet_pass_states', ['merchant_id'])
    op.create_index('ix_wallet_pass_states_state', 'wallet_pass_states', ['state'])
    op.create_index('ix_wallet_pass_states_expires_at', 'wallet_pass_states', ['expires_at'])
    op.create_index('idx_wallet_pass_session_merchant', 'wallet_pass_states', ['session_id', 'merchant_id'])
    op.create_index('idx_wallet_pass_expires', 'wallet_pass_states', ['expires_at'])


def downgrade() -> None:
    """Drop wallet_pass_states table"""
    op.drop_index('idx_wallet_pass_expires', table_name='wallet_pass_states')
    op.drop_index('idx_wallet_pass_session_merchant', table_name='wallet_pass_states')
    op.drop_index('ix_wallet_pass_states_expires_at', table_name='wallet_pass_states')
    op.drop_index('ix_wallet_pass_states_state', table_name='wallet_pass_states')
    op.drop_index('ix_wallet_pass_states_merchant_id', table_name='wallet_pass_states')
    op.drop_index('ix_wallet_pass_states_session_id', table_name='wallet_pass_states')
    op.drop_table('wallet_pass_states')

