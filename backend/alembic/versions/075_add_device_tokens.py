"""Add device_tokens table for FCM/APNs push notification tokens

Revision ID: 075_device_tokens
Revises: 074_campaign_pivot
Create Date: 2026-02-24
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

# revision identifiers
revision = '075_device_tokens'
down_revision = '074_campaign_pivot'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'device_tokens' not in existing_tables:
        op.create_table(
            'device_tokens',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('token', sa.String(512), nullable=False),
            sa.Column('platform', sa.String(10), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    try:
        op.create_index('idx_device_token_user', 'device_tokens', ['user_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_device_token_token', 'device_tokens', ['token'], unique=True)
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('idx_device_token_token', table_name='device_tokens')
    op.drop_index('idx_device_token_user', table_name='device_tokens')
    op.drop_table('device_tokens')
