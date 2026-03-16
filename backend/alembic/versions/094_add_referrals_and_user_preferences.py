"""Add referral tables and user notification preferences

Revision ID: 094_add_referrals_and_user_preferences
Revises: 093_add_charger_pricing_score_favorites
Create Date: 2026-03-03

Adds:
- referral_codes table
- referral_redemptions table
- notifications_enabled and email_marketing columns to users
"""
from alembic import op
import sqlalchemy as sa

revision = "094_add_referrals_and_user_preferences"
down_revision = "093_add_charger_pricing_score_favorites"
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
    # User preference columns
    if not _column_exists("users", "notifications_enabled"):
        op.add_column("users", sa.Column("notifications_enabled", sa.Boolean(), server_default="1", nullable=False))
    if not _column_exists("users", "email_marketing"):
        op.add_column("users", sa.Column("email_marketing", sa.Boolean(), server_default="0", nullable=False))

    # Referral codes
    if not _table_exists("referral_codes"):
        op.create_table(
            "referral_codes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
            sa.Column("code", sa.String(20), nullable=False, unique=True, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    # Referral redemptions
    if not _table_exists("referral_redemptions"):
        op.create_table(
            "referral_redemptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("referral_code_id", sa.Integer(), sa.ForeignKey("referral_codes.id"), nullable=False),
            sa.Column("referred_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
            sa.Column("redeemed_at", sa.DateTime(), nullable=False),
            sa.Column("reward_granted", sa.Boolean(), server_default="0", nullable=False),
        )


def downgrade() -> None:
    op.drop_table("referral_redemptions")
    op.drop_table("referral_codes")
    op.drop_column("users", "email_marketing")
    op.drop_column("users", "notifications_enabled")
