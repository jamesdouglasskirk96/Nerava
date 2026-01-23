"""add wallet locks

Revision ID: 034_add_wallet_locks
Revises: 033_make_idempotency_keys_unique
Create Date: 2024-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '034_add_wallet_locks'
down_revision = '033_make_idempotency_keys_unique'
branch_labels = None
depends_on = None


def upgrade():
    # Create wallet_locks table for concurrency control
    # Used with SELECT ... FOR UPDATE to prevent race conditions in balance operations
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'wallet_locks' not in tables:
        op.create_table('wallet_locks',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('user_id')
        )
        op.create_index('ix_wallet_locks_user_id', 'wallet_locks', ['user_id'])


def downgrade():
    op.drop_index('ix_wallet_locks_user_id', table_name='wallet_locks')
    op.drop_table('wallet_locks')








