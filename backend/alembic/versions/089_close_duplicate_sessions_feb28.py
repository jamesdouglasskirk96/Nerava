"""Close stuck duplicate session_events from Feb 28 2026 12:51-12:56 UTC batch.

Migration 088 cleaned sessions before 12:00 UTC but missed the 12:51-12:56
batch that was created by the same source_session_id duplication bug.

This migration closes all session_events where:
- session_end IS NULL
- session_start between 2026-02-28T12:00:00 and 2026-02-28T13:00:00

Sets session_end = session_start + 5 min, quality_score = 0,
ended_reason = 'duplicate_cleanup'.

Revision ID: 089_close_duplicate_sessions_feb28
Revises: 088_close_stale_sessions
Create Date: 2026-02-28
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = '089_close_duplicate_sessions_feb28'
down_revision = '088_close_stale_sessions'
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
            SET session_end = session_start + interval '5 minutes',
                quality_score = 0,
                ended_reason = 'duplicate_cleanup',
                updated_at = NOW()
            WHERE session_end IS NULL
              AND session_start >= '2026-02-28T12:00:00'
              AND session_start < '2026-02-28T13:00:00'
        """))
    else:
        # SQLite fallback for tests
        op.execute(text("""
            UPDATE session_events
            SET session_end = datetime(session_start, '+5 minutes'),
                quality_score = 0,
                ended_reason = 'duplicate_cleanup',
                updated_at = datetime('now')
            WHERE session_end IS NULL
              AND session_start >= '2026-02-28T12:00:00'
              AND session_start < '2026-02-28T13:00:00'
        """))


def downgrade():
    # Data migration — cannot reliably undo. The duplicate sessions were
    # invalid artifacts of a bug and should remain closed.
    pass
