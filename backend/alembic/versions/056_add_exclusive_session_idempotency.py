"""Add idempotency_key to exclusive_sessions

Revision ID: 056_add_exclusive_session_idempotency
Revises: 055_add_amenity_votes_table
Create Date: 2026-01-27 18:00:00.000000

Adds idempotency_key column to exclusive_sessions table for P0 race condition fix
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '056_add_exclusive_session_idempotency'
down_revision = '055_add_amenity_votes_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add idempotency_key column and unique index to exclusive_sessions"""
    op.add_column("exclusive_sessions", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.create_index(
        "ix_exclusive_sessions_idempotency_key",
        "exclusive_sessions",
        ["idempotency_key"],
        unique=True
    )


def downgrade() -> None:
    """Remove idempotency_key column and index"""
    op.drop_index("ix_exclusive_sessions_idempotency_key", table_name="exclusive_sessions")
    op.drop_column("exclusive_sessions", "idempotency_key")
