"""vehicle tokens default encrypted

Revision ID: 035_vehicle_tokens_default_encrypted
Revises: 034_add_wallet_locks
Create Date: 2024-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '035_vehicle_tokens_default_encrypted'
down_revision = '034_add_wallet_locks'
branch_labels = None
depends_on = None


def upgrade():
    # Set server_default='1' for encryption_version on new rows only
    # Existing rows remain 0 (plaintext) until backfilled
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    is_sqlite = bind.dialect.name == 'sqlite'

    if 'vehicle_tokens' in tables:
        # Check if column exists
        columns = [col['name'] for col in inspector.get_columns('vehicle_tokens')]
        if 'encryption_version' in columns:
            # SQLite doesn't support ALTER COLUMN for defaults - skip for SQLite
            # The default is handled at the model layer anyway
            if not is_sqlite:
                op.alter_column('vehicle_tokens', 'encryption_version',
                              server_default='1',
                              existing_nullable=False,
                              existing_type=sa.Integer())


def downgrade():
    # Revert to default 0
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    is_sqlite = bind.dialect.name == 'sqlite'

    if 'vehicle_tokens' in tables:
        columns = [col['name'] for col in inspector.get_columns('vehicle_tokens')]
        if 'encryption_version' in columns:
            # SQLite doesn't support ALTER COLUMN for defaults - skip for SQLite
            if not is_sqlite:
                op.alter_column('vehicle_tokens', 'encryption_version',
                              server_default='0',
                              existing_nullable=False,
                              existing_type=sa.Integer())

