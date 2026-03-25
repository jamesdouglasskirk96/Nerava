"""Add charging_session_id and verification_code to exclusive_sessions

Revision ID: 113
Revises: 112
"""
from alembic import op
import sqlalchemy as sa

revision = "113"
down_revision = "112"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("exclusive_sessions", sa.Column("charging_session_id", sa.String(), nullable=True))
    op.add_column("exclusive_sessions", sa.Column("verification_code", sa.String(50), nullable=True))
    op.create_index("ix_exclusive_sessions_charging_session", "exclusive_sessions", ["charging_session_id"])
    op.create_foreign_key(
        "fk_exclusive_sessions_charging_session",
        "exclusive_sessions",
        "session_events",
        ["charging_session_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_exclusive_sessions_charging_session", "exclusive_sessions", type_="foreignkey")
    op.drop_index("ix_exclusive_sessions_charging_session", table_name="exclusive_sessions")
    op.drop_column("exclusive_sessions", "verification_code")
    op.drop_column("exclusive_sessions", "charging_session_id")
