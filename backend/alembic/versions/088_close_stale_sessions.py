"""Close stuck/duplicate session_events from Feb 28 2026 source_session_id bug.

A bug in source_session_id generation (Tesla's per-call changing timestamp)
created 6 duplicate session_events for the same charging session. These all
have session_end = NULL and are stuck open.

This migration closes them by:
- Setting session_end = session_start + duration_minutes (or +30 min fallback)
- Setting quality_score = 0 (invalid / cleaned-up)
- Setting ended_reason = 'duplicate_cleanup'

Only targets rows where session_end IS NULL AND session_start < 2026-02-28 12:00 UTC.

Revision ID: 088_close_stale_sessions
Revises: 087_close_stale_sessions
Create Date: 2026-02-28
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = '088_close_stale_sessions'
down_revision = '087_close_stale_sessions'
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
            SET session_end = CASE
                    WHEN duration_minutes IS NOT NULL AND duration_minutes > 0
                    THEN session_start + (duration_minutes || ' minutes')::interval
                    ELSE session_start + interval '30 minutes'
                END,
                quality_score = 0,
                ended_reason = 'duplicate_cleanup',
                updated_at = NOW()
            WHERE session_end IS NULL
              AND session_start < '2026-02-28T12:00:00'
        """))
    else:
        # SQLite fallback for tests
        op.execute(text("""
            UPDATE session_events
            SET session_end = CASE
                    WHEN duration_minutes IS NOT NULL AND duration_minutes > 0
                    THEN datetime(session_start, '+' || duration_minutes || ' minutes')
                    ELSE datetime(session_start, '+30 minutes')
                END,
                quality_score = 0,
                ended_reason = 'duplicate_cleanup',
                updated_at = datetime('now')
            WHERE session_end IS NULL
              AND session_start < '2026-02-28T12:00:00'
        """))


def downgrade():
    # Data migration — cannot reliably undo. The duplicate sessions were
    # invalid artifacts of a bug and should remain closed.
    pass
