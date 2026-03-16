"""Add email_otp_challenges table for console email OTP auth

Revision ID: 098_add_email_otp_challenges
Revises: 097_add_next_poll_at_to_session_events
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "098_add_email_otp_challenges"
down_revision = "097_add_next_poll_at_to_session_events"
branch_labels = None
depends_on = None


def _table_exists(table):
    """Check if table exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("email_otp_challenges"):
        op.create_table(
            "email_otp_challenges",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("email", sa.String(), nullable=False, index=True),
            sa.Column("code_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("consumed", sa.Boolean(), nullable=False, server_default="0", index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("email_otp_challenges")
