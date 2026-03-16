"""Add ad_impressions table

Revision ID: 102_add_ad_impressions
Revises: 101_add_merchant_subscriptions
"""
from alembic import op
import sqlalchemy as sa

revision = "102_add_ad_impressions"
down_revision = "101_add_merchant_subscriptions"
branch_labels = None
depends_on = None


def _table_exists(table):
    """Check if table exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("ad_impressions"):
        op.create_table(
            "ad_impressions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("merchant_id", sa.String, sa.ForeignKey("domain_merchants.id"), nullable=False),
            sa.Column("place_id", sa.String, nullable=True),
            sa.Column("driver_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("impression_type", sa.String, nullable=False),
            sa.Column("session_id", sa.String, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        )
        try:
            op.create_index("ix_ad_impressions_merchant", "ad_impressions", ["merchant_id"])
        except Exception:
            pass
        try:
            op.create_index("ix_ad_impressions_driver", "ad_impressions", ["driver_user_id"])
        except Exception:
            pass
        try:
            op.create_index("ix_ad_impressions_created", "ad_impressions", ["created_at"])
        except Exception:
            pass
        try:
            op.create_index("ix_ad_impressions_merchant_created", "ad_impressions", ["merchant_id", "created_at"])
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table("ad_impressions")
