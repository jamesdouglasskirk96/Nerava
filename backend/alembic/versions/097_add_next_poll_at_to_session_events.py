"""Add next_poll_at column to session_events for smart poll scheduling

Revision ID: 097_add_next_poll_at_to_session_events
Revises: 096_add_campaign_funding_columns
Create Date: 2026-03-04

Adds next_poll_at TIMESTAMP to session_events so the ScheduledPollWorker
knows when to run the verification poll (poll #2) for each active session.
"""
from alembic import op
import sqlalchemy as sa

revision = "097_add_next_poll_at_to_session_events"
down_revision = "096_add_campaign_funding_columns"
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
    if not _column_exists("session_events", "next_poll_at"):
        op.add_column("session_events", sa.Column("next_poll_at", sa.DateTime(), nullable=True))
    try:
        op.create_index(
            "ix_session_events_next_poll",
            "session_events",
            ["next_poll_at"],
        )
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index("ix_session_events_next_poll", table_name="session_events")
    op.drop_column("session_events", "next_poll_at")
