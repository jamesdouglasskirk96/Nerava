"""Add driver_wallets, payouts, cards, transactions, and merchant_offers tables

Revision ID: 073
Revises: 072
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '073'
down_revision = '072'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'driver_wallets' not in existing_tables:
        op.create_table(
            'driver_wallets',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
            sa.Column('balance_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('pending_balance_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('stripe_account_id', sa.String(255), nullable=True),
            sa.Column('stripe_account_status', sa.String(50), nullable=True),
            sa.Column('stripe_onboarding_complete', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('total_earned_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_withdrawn_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_driver_wallet_driver', 'driver_wallets', ['driver_id'])
        op.create_index('idx_driver_wallet_stripe', 'driver_wallets', ['stripe_account_id'])

    if 'payouts' not in existing_tables:
        op.create_table(
            'payouts',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('wallet_id', sa.String(36), sa.ForeignKey('driver_wallets.id'), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('stripe_transfer_id', sa.String(255), nullable=True),
            sa.Column('stripe_payout_id', sa.String(255), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('failure_reason', sa.String(500), nullable=True),
            sa.Column('idempotency_key', sa.String(100), unique=True, nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_payout_driver', 'payouts', ['driver_id'])
        op.create_index('idx_payout_status', 'payouts', ['status'])
        op.create_index('idx_payout_stripe_transfer', 'payouts', ['stripe_transfer_id'])

    if 'cards' not in existing_tables:
        op.create_table(
            'cards',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('fidel_card_id', sa.String(255), nullable=True),
            sa.Column('last4', sa.String(4), nullable=False),
            sa.Column('brand', sa.String(20), nullable=False),
            sa.Column('fingerprint', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('linked_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('idx_card_driver', 'cards', ['driver_id'])
        op.create_index('idx_card_fidel', 'cards', ['fidel_card_id'])
        op.create_index('idx_card_fingerprint', 'cards', ['fingerprint'])

    if 'merchant_offers' not in existing_tables:
        op.create_table(
            'merchant_offers',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('merchant_id', sa.String(36), nullable=False),
            sa.Column('fidel_offer_id', sa.String(255), nullable=True),
            sa.Column('fidel_program_id', sa.String(255), nullable=True),
            sa.Column('min_spend_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reward_cents', sa.Integer(), nullable=False),
            sa.Column('reward_percent', sa.Integer(), nullable=True),
            sa.Column('max_reward_cents', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('valid_from', sa.DateTime(), nullable=True),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_merchant_offer_merchant', 'merchant_offers', ['merchant_id'])
        op.create_index('idx_merchant_offer_active', 'merchant_offers', ['is_active'])
        op.create_index('idx_merchant_offer_fidel', 'merchant_offers', ['fidel_offer_id'])

    if 'clo_transactions' not in existing_tables:
        op.create_table(
            'clo_transactions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('card_id', sa.String(36), sa.ForeignKey('cards.id'), nullable=False),
            sa.Column('merchant_id', sa.String(36), nullable=False),
            sa.Column('offer_id', sa.String(36), sa.ForeignKey('merchant_offers.id'), nullable=True),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('reward_cents', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('external_id', sa.String(255), nullable=True),
            sa.Column('charging_session_id', sa.String(36), nullable=True),
            sa.Column('transaction_time', sa.DateTime(), nullable=False),
            sa.Column('merchant_name', sa.String(255), nullable=True),
            sa.Column('merchant_location', sa.String(500), nullable=True),
            sa.Column('eligibility_reason', sa.String(200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_clo_txn_driver', 'clo_transactions', ['driver_id'])
        op.create_index('idx_clo_txn_card', 'clo_transactions', ['card_id'])
        op.create_index('idx_clo_txn_status', 'clo_transactions', ['status'])
        op.create_index('idx_clo_txn_external', 'clo_transactions', ['external_id'])
        op.create_index('idx_clo_txn_session', 'clo_transactions', ['charging_session_id'])

    if 'wallet_ledger' not in existing_tables:
        op.create_table(
            'wallet_ledger',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('wallet_id', sa.String(36), sa.ForeignKey('driver_wallets.id'), nullable=False),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('balance_after_cents', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(30), nullable=False),
            sa.Column('reference_type', sa.String(30), nullable=True),
            sa.Column('reference_id', sa.String(36), nullable=True),
            sa.Column('description', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('idx_wallet_ledger_wallet', 'wallet_ledger', ['wallet_id'])
        op.create_index('idx_wallet_ledger_driver', 'wallet_ledger', ['driver_id'])
        op.create_index('idx_wallet_ledger_reference', 'wallet_ledger', ['reference_type', 'reference_id'])


def downgrade():
    op.drop_table('wallet_ledger')
    op.drop_table('clo_transactions')
    op.drop_table('merchant_offers')
    op.drop_table('cards')
    op.drop_table('payouts')
    op.drop_table('driver_wallets')
