"""Add tesla_oauth_states table for CSRF state persistence

Revision ID: 078_tesla_oauth_states
Revises: 077_wallet_balance_constraint
Create Date: 2026-02-25
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = '078_tesla_oauth_states'
down_revision = '077_wallet_balance_constraint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'tesla_oauth_states' not in existing_tables:
        op.create_table(
            'tesla_oauth_states',
            sa.Column('state', sa.String(64), primary_key=True),
            sa.Column('data_json', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
        )
    try:
        op.create_index('idx_tesla_oauth_states_expires', 'tesla_oauth_states', ['expires_at'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('idx_tesla_oauth_states_expires', table_name='tesla_oauth_states')
    op.drop_table('tesla_oauth_states')
