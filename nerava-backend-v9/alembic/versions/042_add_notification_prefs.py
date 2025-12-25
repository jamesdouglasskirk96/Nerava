"""Add notification preferences table

Revision ID: 042_add_notification_prefs
Revises: 041_add_redemption_idempotency_key
Create Date: 2025-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '042_add_notification_prefs'
down_revision = '041_add_redemption_idempotency_key'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_notification_prefs table
    op.create_table(
        'user_notification_prefs',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('earned_nova', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('nearby_nova', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('wallet_reminders', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_user_notification_prefs_user_id'), 'user_notification_prefs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_notification_prefs_user_id'), table_name='user_notification_prefs')
    op.drop_table('user_notification_prefs')

