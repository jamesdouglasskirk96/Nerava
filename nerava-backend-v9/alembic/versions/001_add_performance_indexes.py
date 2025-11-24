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


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade():
    # Add indexes for performance (guarded for legacy DBs)
    if _has_table('charge_sessions'):
        op.create_index('idx_sessions_user_id', 'charge_sessions', ['user_id'])
        op.create_index(
            'idx_sessions_active',
            'charge_sessions',
            ['stopped_at'],
            postgresql_where=sa.text('stopped_at IS NULL')
        )
    if _has_table('wallet_transactions'):
        op.create_index('idx_wallet_user_id', 'wallet_transactions', ['user_id'])


def downgrade():
    if _has_table('wallet_transactions'):
        op.drop_index('idx_wallet_user_id', 'wallet_transactions')
    if _has_table('charge_sessions'):
        op.drop_index('idx_sessions_active', 'charge_sessions')
        op.drop_index('idx_sessions_user_id', 'charge_sessions')
