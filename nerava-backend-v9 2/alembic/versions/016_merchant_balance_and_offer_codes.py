"""Add merchant balance and offer code tables

Revision ID: 016
Revises: 015_merge_heads
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015_merge_heads'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    # MerchantBalance table
    if not _has_table('merchant_balance'):
        op.create_table(
            'merchant_balance',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False, unique=True),
            sa.Column('balance_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_merchant_balance_merchant_id', 'merchant_balance', ['merchant_id'], unique=True)

    # MerchantBalanceLedger table
    if not _has_table('merchant_balance_ledger'):
        op.create_table(
            'merchant_balance_ledger',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('delta_cents', sa.Integer(), nullable=False),
            sa.Column('reason', sa.String(), nullable=False),
            sa.Column('session_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_merchant_balance_ledger_merchant_id', 'merchant_balance_ledger', ['merchant_id'])
        op.create_index('ix_merchant_balance_ledger_session_id', 'merchant_balance_ledger', ['session_id'])
        op.create_index('ix_merchant_balance_ledger_created_at', 'merchant_balance_ledger', ['created_at'])
        op.create_index('idx_merchant_balance_ledger_merchant_created', 'merchant_balance_ledger', ['merchant_id', 'created_at'])

    # MerchantOfferCode table
    if not _has_table('merchant_offer_codes'):
        op.create_table(
            'merchant_offer_codes',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('code', sa.String(), nullable=False, unique=True),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('is_redeemed', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_merchant_offer_codes_merchant_id', 'merchant_offer_codes', ['merchant_id'])
        op.create_index('ix_merchant_offer_codes_code', 'merchant_offer_codes', ['code'], unique=True)
        op.create_index('ix_merchant_offer_codes_is_redeemed', 'merchant_offer_codes', ['is_redeemed'])
        op.create_index('ix_merchant_offer_codes_expires_at', 'merchant_offer_codes', ['expires_at'])
        op.create_index('idx_merchant_offer_codes_merchant_created', 'merchant_offer_codes', ['merchant_id', 'created_at'])
        op.create_index('idx_merchant_offer_codes_code_redeemed', 'merchant_offer_codes', ['code', 'is_redeemed'])


def downgrade() -> None:
    if _has_table('merchant_offer_codes'):
        op.drop_table('merchant_offer_codes')
    if _has_table('merchant_balance_ledger'):
        op.drop_table('merchant_balance_ledger')
    if _has_table('merchant_balance'):
        op.drop_table('merchant_balance')

