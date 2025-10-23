"""Add performance indexes

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes for performance
    op.create_index('idx_sessions_user_id', 'charge_sessions', ['user_id'])
    op.create_index('idx_sessions_active', 'charge_sessions', ['stopped_at'], 
                   postgresql_where=sa.text('stopped_at IS NULL'))
    op.create_index('idx_wallet_user_id', 'wallet_transactions', ['user_id'])


def downgrade():
    op.drop_index('idx_wallet_user_id', 'wallet_transactions')
    op.drop_index('idx_sessions_active', 'charge_sessions')
    op.drop_index('idx_sessions_user_id', 'charge_sessions')
