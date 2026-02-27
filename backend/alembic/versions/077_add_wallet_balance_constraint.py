"""Add non-negative balance constraint to driver_wallets

Revision ID: 077_wallet_balance_constraint
Revises: 076_merchant_is_corporate
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

revision = '077_wallet_balance_constraint'
down_revision = '076_merchant_is_corporate'
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.create_check_constraint(
            'ck_wallet_balance_non_negative',
            'driver_wallets',
            'balance_cents >= 0',
        )
    except Exception:
        pass


def downgrade() -> None:
    op.drop_constraint('ck_wallet_balance_non_negative', 'driver_wallets', type_='check')
