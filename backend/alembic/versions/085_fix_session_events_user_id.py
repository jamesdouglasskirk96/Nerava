"""Fix session_events: make user_id nullable, copy driver_user_id values

The session_events table was originally created with a user_id NOT NULL column
by metadata.create_all(). Migration 083 added driver_user_id as a separate column.
The ORM model uses driver_user_id, leaving user_id null and causing NOT NULL violations.

Fix: make user_id nullable and keep driver_user_id as the canonical column.

Revision ID: 085_fix_session_user_id
Revises: 084_fix_campaigns
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = '085_fix_session_user_id'
down_revision = '084_fix_campaigns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'session_events' not in existing_tables:
        return

    columns = {c['name'] for c in inspector.get_columns('session_events')}

    # Make user_id nullable if it exists
    if 'user_id' in columns:
        op.alter_column('session_events', 'user_id',
                        existing_type=sa.Integer(),
                        nullable=True)
        print("  Made session_events.user_id nullable")

        # Copy driver_user_id -> user_id where user_id is null (for consistency)
        if 'driver_user_id' in columns:
            op.execute(
                "UPDATE session_events SET user_id = driver_user_id "
                "WHERE user_id IS NULL AND driver_user_id IS NOT NULL"
            )
            print("  Backfilled user_id from driver_user_id")


def downgrade() -> None:
    pass
