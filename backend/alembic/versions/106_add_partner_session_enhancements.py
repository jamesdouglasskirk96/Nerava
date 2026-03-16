"""Add partner session enhancements (status, signal, vehicle info)

Revision ID: 106
Revises: 105
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "106_add_partner_session_enhancements"
down_revision = "105_add_partner_fields"


def _column_exists(table, column):
    """Check if column exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade():
    if not _column_exists("session_events", "partner_status"):
        op.add_column("session_events", sa.Column("partner_status", sa.String(30), nullable=True))
    if not _column_exists("session_events", "signal_confidence"):
        op.add_column("session_events", sa.Column("signal_confidence", sa.Float(), nullable=True))
    if not _column_exists("session_events", "vehicle_make"):
        op.add_column("session_events", sa.Column("vehicle_make", sa.String(), nullable=True))
    if not _column_exists("session_events", "vehicle_model"):
        op.add_column("session_events", sa.Column("vehicle_model", sa.String(), nullable=True))
    if not _column_exists("session_events", "vehicle_year"):
        op.add_column("session_events", sa.Column("vehicle_year", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column("session_events", "vehicle_year")
    op.drop_column("session_events", "vehicle_model")
    op.drop_column("session_events", "vehicle_make")
    op.drop_column("session_events", "signal_confidence")
    op.drop_column("session_events", "partner_status")
