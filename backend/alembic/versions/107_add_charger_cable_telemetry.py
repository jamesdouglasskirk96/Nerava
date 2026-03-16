"""Add charger cable/adapter telemetry fields to session_events

Captures Tesla charge_state fields that identify CCS adapters (EVject, etc.),
charger brand, voltage, and current for richer session data.

Revision ID: 107
Revises: 106
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = "107_add_charger_cable_telemetry"
down_revision = "106_add_partner_session_enhancements"


def _column_exists(table, column):
    """Check if column exists (works on both PostgreSQL and SQLite)."""
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade():
    if not _column_exists("session_events", "conn_charge_cable"):
        op.add_column("session_events", sa.Column("conn_charge_cable", sa.String(50), nullable=True))
    if not _column_exists("session_events", "fast_charger_brand"):
        op.add_column("session_events", sa.Column("fast_charger_brand", sa.String(100), nullable=True))
    if not _column_exists("session_events", "charger_voltage"):
        op.add_column("session_events", sa.Column("charger_voltage", sa.Float(), nullable=True))
    if not _column_exists("session_events", "charger_actual_current"):
        op.add_column("session_events", sa.Column("charger_actual_current", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("session_events", "charger_actual_current")
    op.drop_column("session_events", "charger_voltage")
    op.drop_column("session_events", "fast_charger_brand")
    op.drop_column("session_events", "conn_charge_cable")
