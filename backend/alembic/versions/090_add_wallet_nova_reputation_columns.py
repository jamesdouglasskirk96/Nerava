"""Add nova_balance and energy_reputation_score columns to driver_wallets

These columns existed in the original migration 018 schema but were lost when
migration 073 recreated the table with CREATE TABLE IF NOT EXISTS using a
different schema. Production driver_wallets is missing these columns.

Revision ID: 090_add_wallet_nova_reputation_columns
Revises: 089_close_duplicate_sessions_feb28
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = '090_add_wallet_nova_reputation_columns'
down_revision = '089_close_duplicate_sessions_feb28'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        # PostgreSQL supports IF NOT EXISTS on ADD COLUMN (v9.6+)
        conn.execute(sa.text(
            "ALTER TABLE driver_wallets ADD COLUMN IF NOT EXISTS "
            "nova_balance INTEGER NOT NULL DEFAULT 0"
        ))
        conn.execute(sa.text(
            "ALTER TABLE driver_wallets ADD COLUMN IF NOT EXISTS "
            "energy_reputation_score INTEGER NOT NULL DEFAULT 0"
        ))
    else:
        # SQLite: check if columns exist via PRAGMA
        cols = [row[1] for row in conn.execute(sa.text(
            "PRAGMA table_info('driver_wallets')"
        )).fetchall()]
        if "nova_balance" not in cols:
            conn.execute(sa.text(
                "ALTER TABLE driver_wallets ADD COLUMN "
                "nova_balance INTEGER NOT NULL DEFAULT 0"
            ))
        if "energy_reputation_score" not in cols:
            conn.execute(sa.text(
                "ALTER TABLE driver_wallets ADD COLUMN "
                "energy_reputation_score INTEGER NOT NULL DEFAULT 0"
            ))


def downgrade():
    # PostgreSQL supports DROP COLUMN; SQLite does not easily
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text(
            "ALTER TABLE driver_wallets DROP COLUMN IF EXISTS nova_balance"
        ))
        conn.execute(sa.text(
            "ALTER TABLE driver_wallets DROP COLUMN IF EXISTS energy_reputation_score"
        ))
