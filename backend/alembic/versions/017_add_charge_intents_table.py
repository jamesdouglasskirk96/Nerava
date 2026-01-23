"""Add charge_intents table for Earn page

Revision ID: 017
Revises: 016
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = insp.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    # ChargeIntents table - stores user's saved charge intents for the Earn page
    if not _has_table('charge_intents'):
        op.create_table(
            'charge_intents',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('station_id', sa.String(), nullable=True),
            sa.Column('station_name', sa.String(), nullable=True),
            sa.Column('merchant_name', sa.String(), nullable=True),
            sa.Column('merchant', sa.String(), nullable=True),  # Alternative merchant name field
            sa.Column('perk_title', sa.String(), nullable=True),
            sa.Column('perk_id', sa.String(), nullable=True),
            sa.Column('address', sa.String(), nullable=True),
            sa.Column('eta_minutes', sa.Integer(), nullable=True),
            sa.Column('window_text', sa.String(), nullable=True),
            sa.Column('distance_text', sa.String(), nullable=True),
            sa.Column('starts_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='saved'),
            sa.Column('merchant_lat', sa.Float(), nullable=True),
            sa.Column('merchant_lng', sa.Float(), nullable=True),
            sa.Column('station_lat', sa.Float(), nullable=True),
            sa.Column('station_lng', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
    
    # Create indexes if they don't exist
    if _has_table('charge_intents'):
        if not _has_index('charge_intents', 'ix_charge_intents_user_id'):
            op.create_index('ix_charge_intents_user_id', 'charge_intents', ['user_id'])
        if not _has_index('charge_intents', 'ix_charge_intents_status'):
            op.create_index('ix_charge_intents_status', 'charge_intents', ['status'])
        if not _has_index('charge_intents', 'ix_charge_intents_created_at'):
            op.create_index('ix_charge_intents_created_at', 'charge_intents', ['created_at'])


def downgrade() -> None:
    if _has_table('charge_intents'):
        op.drop_table('charge_intents')

