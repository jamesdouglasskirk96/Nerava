"""No-op: superseded by migration 082

Revision ID: 081_credit_wallet_retry
Revises: 080_credit_wallet
Create Date: 2026-02-26
"""
from alembic import op

revision = '081_credit_wallet_retry'
down_revision = '080_credit_wallet'
branch_labels = None
depends_on = None


def upgrade():
    # Superseded by migration 082
    pass


def downgrade():
    pass
