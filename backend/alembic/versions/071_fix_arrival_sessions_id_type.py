"""Fix arrival_sessions.id column type to UUID

Revision ID: 071
Revises: 070
Create Date: 2026-02-10

The arrival_sessions.id column was created as VARCHAR(36) but the model uses
UUIDType() which expects PostgreSQL's native UUID type. This migration alters
the column type to use native UUID.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '071'
down_revision = '070'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == 'postgresql':
        # Drop ALL foreign key constraints that reference arrival_sessions.id
        op.execute(sa.text("""
            ALTER TABLE billing_events
            DROP CONSTRAINT IF EXISTS billing_events_arrival_session_id_fkey
        """))
        op.execute(sa.text("""
            ALTER TABLE queued_orders
            DROP CONSTRAINT IF EXISTS queued_orders_arrival_session_id_fkey
        """))
        op.execute(sa.text("""
            ALTER TABLE car_pins
            DROP CONSTRAINT IF EXISTS car_pins_used_by_session_id_fkey
        """))

        # Convert arrival_sessions.id column from VARCHAR(36) to UUID
        op.execute(sa.text("""
            ALTER TABLE arrival_sessions
            ALTER COLUMN id TYPE UUID USING id::uuid
        """))

        # Convert billing_events columns
        op.execute(sa.text("""
            ALTER TABLE billing_events
            ALTER COLUMN id TYPE UUID USING id::uuid
        """))
        op.execute(sa.text("""
            ALTER TABLE billing_events
            ALTER COLUMN arrival_session_id TYPE UUID USING arrival_session_id::uuid
        """))

        # Convert queued_orders arrival_session_id column
        op.execute(sa.text("""
            ALTER TABLE queued_orders
            ALTER COLUMN arrival_session_id TYPE UUID USING arrival_session_id::uuid
        """))

        # Convert car_pins used_by_session_id column
        op.execute(sa.text("""
            ALTER TABLE car_pins
            ALTER COLUMN used_by_session_id TYPE UUID USING used_by_session_id::uuid
        """))

        # Recreate the foreign key constraints
        op.execute(sa.text("""
            ALTER TABLE billing_events
            ADD CONSTRAINT billing_events_arrival_session_id_fkey
            FOREIGN KEY (arrival_session_id) REFERENCES arrival_sessions(id)
        """))
        op.execute(sa.text("""
            ALTER TABLE queued_orders
            ADD CONSTRAINT queued_orders_arrival_session_id_fkey
            FOREIGN KEY (arrival_session_id) REFERENCES arrival_sessions(id)
        """))
        op.execute(sa.text("""
            ALTER TABLE car_pins
            ADD CONSTRAINT car_pins_used_by_session_id_fkey
            FOREIGN KEY (used_by_session_id) REFERENCES arrival_sessions(id)
        """))


def downgrade():
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == 'postgresql':
        # Convert back to VARCHAR(36)
        op.execute(sa.text("""
            ALTER TABLE arrival_sessions
            ALTER COLUMN id TYPE VARCHAR(36) USING id::text
        """))

        try:
            op.execute(sa.text("""
                ALTER TABLE billing_events
                ALTER COLUMN id TYPE VARCHAR(36) USING id::text
            """))
            op.execute(sa.text("""
                ALTER TABLE billing_events
                ALTER COLUMN arrival_session_id TYPE VARCHAR(36) USING arrival_session_id::text
            """))
        except Exception:
            pass
