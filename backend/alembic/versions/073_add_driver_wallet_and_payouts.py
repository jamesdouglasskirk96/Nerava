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
    """Create tables using raw SQL with IF NOT EXISTS for maximum safety."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS driver_wallets (
            id VARCHAR(36) PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
            balance_cents INTEGER NOT NULL DEFAULT 0,
            pending_balance_cents INTEGER NOT NULL DEFAULT 0,
            stripe_account_id VARCHAR(255),
            stripe_account_status VARCHAR(50),
            stripe_onboarding_complete BOOLEAN NOT NULL DEFAULT false,
            total_earned_cents INTEGER NOT NULL DEFAULT 0,
            total_withdrawn_cents INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS payouts (
            id VARCHAR(36) PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES users(id),
            wallet_id VARCHAR(36) NOT NULL,
            amount_cents INTEGER NOT NULL,
            stripe_transfer_id VARCHAR(255),
            stripe_payout_id VARCHAR(255),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            failure_reason VARCHAR(500),
            idempotency_key VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP,
            paid_at TIMESTAMP
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS cards (
            id VARCHAR(36) PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES users(id),
            fidel_card_id VARCHAR(255),
            last4 VARCHAR(4) NOT NULL,
            brand VARCHAR(20) NOT NULL,
            fingerprint VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT true,
            linked_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS merchant_offers (
            id VARCHAR(36) PRIMARY KEY,
            merchant_id VARCHAR(36) NOT NULL,
            fidel_offer_id VARCHAR(255),
            fidel_program_id VARCHAR(255),
            min_spend_cents INTEGER NOT NULL DEFAULT 0,
            reward_cents INTEGER NOT NULL,
            reward_percent INTEGER,
            max_reward_cents INTEGER,
            is_active BOOLEAN NOT NULL DEFAULT true,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS clo_transactions (
            id VARCHAR(36) PRIMARY KEY,
            driver_id INTEGER NOT NULL,
            card_id VARCHAR(36) NOT NULL,
            merchant_id VARCHAR(36) NOT NULL,
            offer_id VARCHAR(36),
            amount_cents INTEGER NOT NULL,
            reward_cents INTEGER,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            external_id VARCHAR(255),
            charging_session_id VARCHAR(36),
            transaction_time TIMESTAMP NOT NULL,
            merchant_name VARCHAR(255),
            merchant_location VARCHAR(500),
            eligibility_reason VARCHAR(200),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            processed_at TIMESTAMP
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS wallet_ledger (
            id VARCHAR(36) PRIMARY KEY,
            wallet_id VARCHAR(36) NOT NULL,
            driver_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL,
            balance_after_cents INTEGER NOT NULL,
            transaction_type VARCHAR(30) NOT NULL,
            reference_type VARCHAR(30),
            reference_id VARCHAR(36),
            description VARCHAR(500),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """))

    # Create indexes safely (ignore if they already exist)
    indexes = [
        ("idx_driver_wallet_driver", "driver_wallets", "driver_id"),
        ("idx_driver_wallet_stripe", "driver_wallets", "stripe_account_id"),
        ("idx_payout_driver", "payouts", "driver_id"),
        ("idx_payout_status", "payouts", "status"),
        ("idx_payout_stripe_transfer", "payouts", "stripe_transfer_id"),
        ("idx_card_driver", "cards", "driver_id"),
        ("idx_card_fidel", "cards", "fidel_card_id"),
        ("idx_card_fingerprint", "cards", "fingerprint"),
        ("idx_merchant_offer_merchant", "merchant_offers", "merchant_id"),
        ("idx_merchant_offer_active", "merchant_offers", "is_active"),
        ("idx_merchant_offer_fidel", "merchant_offers", "fidel_offer_id"),
        ("idx_clo_txn_driver", "clo_transactions", "driver_id"),
        ("idx_clo_txn_card", "clo_transactions", "card_id"),
        ("idx_clo_txn_status", "clo_transactions", "status"),
        ("idx_clo_txn_external", "clo_transactions", "external_id"),
        ("idx_clo_txn_session", "clo_transactions", "charging_session_id"),
        ("idx_wallet_ledger_wallet", "wallet_ledger", "wallet_id"),
        ("idx_wallet_ledger_driver", "wallet_ledger", "driver_id"),
    ]
    for idx_name, table, column in indexes:
        conn.execute(sa.text(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"
        ))

    # Composite index
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_wallet_ledger_reference ON wallet_ledger (reference_type, reference_id)"
    ))


def downgrade():
    op.drop_table('wallet_ledger')
    op.drop_table('clo_transactions')
    op.drop_table('merchant_offers')
    op.drop_table('cards')
    op.drop_table('payouts')
    op.drop_table('driver_wallets')
