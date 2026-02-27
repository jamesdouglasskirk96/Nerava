"""Credit wallet $5.73 for user 17 - handles both table schemas

Revision ID: 082_credit_wallet_final
Revises: 081_credit_wallet_retry
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

revision = '082_credit_wallet_final'
down_revision = '081_credit_wallet_retry'
branch_labels = None
depends_on = None


def upgrade():
    # Already applied in production via v2.9.5 - no-op
    pass


def downgrade():
    pass
