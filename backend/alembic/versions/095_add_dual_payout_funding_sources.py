"""Add dual payout provider support and funding sources

Revision ID: 095_add_dual_payout_funding_sources
Revises: 094_add_referrals_and_user_preferences
Create Date: 2026-03-03

Adds:
- payout_provider, external_account_id, bank_verified to driver_wallets
- payout_provider, external_transfer_id, funding_source_id to payouts
- funding_sources table for Plaid-linked bank accounts
"""
from alembic import op
import sqlalchemy as sa

revision = "095_add_dual_payout_funding_sources"
down_revision = "094_add_referrals_and_user_preferences"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    """Check if column exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def _table_exists(table):
    """Check if table exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    # Driver wallet dual-provider columns
    if not _column_exists("driver_wallets", "payout_provider"):
        op.add_column("driver_wallets", sa.Column("payout_provider", sa.String(20), server_default="stripe", nullable=False))
    if not _column_exists("driver_wallets", "external_account_id"):
        op.add_column("driver_wallets", sa.Column("external_account_id", sa.String(500), nullable=True))
    if not _column_exists("driver_wallets", "bank_verified"):
        op.add_column("driver_wallets", sa.Column("bank_verified", sa.Boolean(), server_default="0", nullable=False))

    # Payout dual-provider columns
    if not _column_exists("payouts", "payout_provider"):
        op.add_column("payouts", sa.Column("payout_provider", sa.String(20), server_default="stripe", nullable=False))
    if not _column_exists("payouts", "external_transfer_id"):
        op.add_column("payouts", sa.Column("external_transfer_id", sa.String(500), nullable=True))
    if not _column_exists("payouts", "funding_source_id"):
        op.add_column("payouts", sa.Column("funding_source_id", sa.String(36), nullable=True))

    # Funding sources table
    if not _table_exists("funding_sources"):
        op.create_table(
            "funding_sources",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("provider", sa.String(20), nullable=False, server_default="dwolla"),
            sa.Column("external_id", sa.String(500), nullable=False),
            sa.Column("institution_name", sa.String(255), nullable=True),
            sa.Column("account_mask", sa.String(10), nullable=True),
            sa.Column("account_type", sa.String(50), nullable=True),
            sa.Column("is_default", sa.Boolean(), server_default="1", nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("removed_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("funding_sources")
    op.drop_column("payouts", "funding_source_id")
    op.drop_column("payouts", "external_transfer_id")
    op.drop_column("payouts", "payout_provider")
    op.drop_column("driver_wallets", "bank_verified")
    op.drop_column("driver_wallets", "external_account_id")
    op.drop_column("driver_wallets", "payout_provider")
