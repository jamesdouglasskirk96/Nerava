"""Add merchant_oauth_tokens table

Revision ID: 099_add_merchant_oauth_tokens
Revises: 098_add_email_otp_challenges
"""
from alembic import op
import sqlalchemy as sa

revision = "099_add_merchant_oauth_tokens"
down_revision = "098_add_email_otp_challenges"
branch_labels = None
depends_on = None


def _table_exists(table):
    """Check if table exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("merchant_oauth_tokens"):
        bind = op.get_bind()
        dialect_name = bind.dialect.name
        uuid_type = sa.String(36) if dialect_name == "sqlite" else sa.UUID()

        op.create_table(
            "merchant_oauth_tokens",
            sa.Column("id", uuid_type, primary_key=True),
            sa.Column("merchant_account_id", uuid_type, sa.ForeignKey("merchant_accounts.id"), nullable=False),
            sa.Column("provider", sa.String, nullable=False, server_default="google_gbp"),
            sa.Column("access_token_encrypted", sa.Text, nullable=True),
            sa.Column("refresh_token_encrypted", sa.Text, nullable=True),
            sa.Column("token_expiry", sa.DateTime, nullable=True),
            sa.Column("scopes", sa.String, nullable=True),
            sa.Column("gbp_account_id", sa.String, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=True),
        )
        try:
            op.create_index("ix_merchant_oauth_tokens_account", "merchant_oauth_tokens", ["merchant_account_id"])
        except Exception:
            pass
        try:
            op.create_index(
                "uq_merchant_oauth_account_provider",
                "merchant_oauth_tokens",
                ["merchant_account_id", "provider"],
                unique=True,
            )
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table("merchant_oauth_tokens")
