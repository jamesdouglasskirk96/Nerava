"""Add campaign funding columns for Stripe checkout deposit

Revision ID: 096_add_campaign_funding_columns
Revises: 095_add_dual_payout_funding_sources
Create Date: 2026-03-03

Adds funding_status, stripe_checkout_session_id, stripe_payment_intent_id, funded_at
to campaigns table. Backfills existing active/paused/exhausted/completed campaigns as funded.
"""
from alembic import op
import sqlalchemy as sa

revision = "096_add_campaign_funding_columns"
down_revision = "095_add_dual_payout_funding_sources"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    """Check if column exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade() -> None:
    if not _column_exists("campaigns", "funding_status"):
        op.add_column("campaigns", sa.Column("funding_status", sa.String(20), nullable=False, server_default="unfunded"))
    if not _column_exists("campaigns", "stripe_checkout_session_id"):
        op.add_column("campaigns", sa.Column("stripe_checkout_session_id", sa.String(255), nullable=True))
    if not _column_exists("campaigns", "stripe_payment_intent_id"):
        op.add_column("campaigns", sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True))
    if not _column_exists("campaigns", "funded_at"):
        op.add_column("campaigns", sa.Column("funded_at", sa.DateTime(), nullable=True))

    # Backfill: existing active/paused/exhausted/completed campaigns are already funded
    op.execute(
        "UPDATE campaigns SET funding_status = 'funded' "
        "WHERE status IN ('active', 'paused', 'exhausted', 'completed')"
    )


def downgrade() -> None:
    op.drop_column("campaigns", "funded_at")
    op.drop_column("campaigns", "stripe_payment_intent_id")
    op.drop_column("campaigns", "stripe_checkout_session_id")
    op.drop_column("campaigns", "funding_status")
