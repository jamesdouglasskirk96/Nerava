"""Add profile columns to domain_merchants

Revision ID: 100_add_merchant_profile_columns
Revises: 099_add_merchant_oauth_tokens
"""
from alembic import op
import sqlalchemy as sa

revision = "100_add_merchant_profile_columns"
down_revision = "099_add_merchant_oauth_tokens"
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
    if not _column_exists("domain_merchants", "description"):
        op.add_column("domain_merchants", sa.Column("description", sa.Text, nullable=True))
    if not _column_exists("domain_merchants", "website"):
        op.add_column("domain_merchants", sa.Column("website", sa.String(512), nullable=True))
    if not _column_exists("domain_merchants", "hours_text"):
        op.add_column("domain_merchants", sa.Column("hours_text", sa.String(512), nullable=True))
    if not _column_exists("domain_merchants", "photo_url"):
        op.add_column("domain_merchants", sa.Column("photo_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("domain_merchants", "photo_url")
    op.drop_column("domain_merchants", "hours_text")
    op.drop_column("domain_merchants", "website")
    op.drop_column("domain_merchants", "description")
