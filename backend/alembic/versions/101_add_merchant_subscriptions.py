"""Add merchant_subscriptions table

Revision ID: 101_add_merchant_subscriptions
Revises: 100_add_merchant_profile_columns
"""
from alembic import op
import sqlalchemy as sa

revision = "101_add_merchant_subscriptions"
down_revision = "100_add_merchant_profile_columns"
branch_labels = None
depends_on = None


def _table_exists(table):
    """Check if table exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("merchant_subscriptions"):
        bind = op.get_bind()
        dialect_name = bind.dialect.name
        uuid_type = sa.String(36) if dialect_name == "sqlite" else sa.UUID()

        op.create_table(
            "merchant_subscriptions",
            sa.Column("id", uuid_type, primary_key=True),
            sa.Column("merchant_account_id", uuid_type, sa.ForeignKey("merchant_accounts.id"), nullable=False),
            sa.Column("place_id", sa.String, nullable=True),
            sa.Column("plan", sa.String, nullable=False),
            sa.Column("status", sa.String, nullable=False, server_default="active"),
            sa.Column("stripe_subscription_id", sa.String, nullable=True, unique=True),
            sa.Column("stripe_customer_id", sa.String, nullable=True),
            sa.Column("current_period_start", sa.DateTime, nullable=True),
            sa.Column("current_period_end", sa.DateTime, nullable=True),
            sa.Column("canceled_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=True),
        )
        try:
            op.create_index("ix_merchant_subscriptions_account", "merchant_subscriptions", ["merchant_account_id"])
        except Exception:
            pass
        try:
            op.create_index("ix_merchant_subscriptions_place", "merchant_subscriptions", ["place_id"])
        except Exception:
            pass
        try:
            op.create_index("ix_merchant_sub_account_plan", "merchant_subscriptions", ["merchant_account_id", "plan"])
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table("merchant_subscriptions")
