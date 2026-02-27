"""Close stale charging sessions that were never ended.

Sets session_end = NOW(), computes duration_minutes, and marks
ended_reason = 'stale_cleanup' for any session_events rows where
session_end IS NULL.

Revision ID: 087_close_stale_sessions
Revises: 086_update_perk_titles
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = '087_close_stale_sessions'
down_revision = '086_update_perk_titles'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    if 'session_events' not in inspector.get_table_names():
        return

    dialect = bind.dialect.name

    if dialect == 'postgresql':
        op.execute(text("""
            UPDATE session_events
            SET session_end = NOW(),
                duration_minutes = EXTRACT(EPOCH FROM (NOW() - session_start))::int / 60,
                ended_reason = 'stale_cleanup',
                updated_at = NOW()
            WHERE session_end IS NULL
        """))
    else:
        # SQLite
        op.execute(text("""
            UPDATE session_events
            SET session_end = datetime('now'),
                duration_minutes = CAST((julianday('now') - julianday(session_start)) * 1440 AS INTEGER),
                ended_reason = 'stale_cleanup',
                updated_at = datetime('now')
            WHERE session_end IS NULL
        """))


def downgrade():
    # Cannot reliably undo — we don't know which sessions were genuinely open.
    pass
