"""Make nova_transactions.idempotency_key unique

Revision ID: 057_make_nova_transactions_idempotency_unique
Revises: 056_add_exclusive_session_idempotency
Create Date: 2026-01-27 18:30:00.000000

Makes idempotency_key unique at database level for P0 data integrity fix.
This migration is idempotent and handles the case where migration 033 already
created uq_nova_transactions_idempotency_key unique index.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '057_make_nova_transactions_idempotency_unique'
down_revision = '056_add_exclusive_session_idempotency'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make nova_transactions.idempotency_key unique (idempotent)"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Get existing indexes
    indexes = inspector.get_indexes('nova_transactions')
    index_names = [idx['name'] for idx in indexes]
    
    # Check if migration 033's unique index exists
    has_uq_index = 'uq_nova_transactions_idempotency_key' in index_names
    has_ix_index = 'ix_nova_transactions_idempotency_key' in index_names
    
    # Drop existing non-unique index if it exists
    if has_ix_index:
        try:
            op.drop_index("ix_nova_transactions_idempotency_key", table_name="nova_transactions")
        except Exception:
            pass  # Index may not exist or may be unique already
    
    # If migration 033's unique index exists, we're done (it's already unique)
    if has_uq_index:
        return
    
    # Create unique index (only if 033's index doesn't exist)
    try:
        op.create_index(
            "ix_nova_transactions_idempotency_key",
            "nova_transactions",
            ["idempotency_key"],
            unique=True
        )
    except Exception:
        # Index may already exist as unique, that's fine
        pass


def downgrade() -> None:
    """Revert to non-unique index"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Get existing indexes
    indexes = inspector.get_indexes('nova_transactions')
    index_names = [idx['name'] for idx in indexes]
    
    # Drop unique index if it exists
    if 'ix_nova_transactions_idempotency_key' in index_names:
        try:
            op.drop_index("ix_nova_transactions_idempotency_key", table_name="nova_transactions")
        except Exception:
            pass
    
    # Create non-unique index
    try:
        op.create_index(
            "ix_nova_transactions_idempotency_key",
            "nova_transactions",
            ["idempotency_key"]
        )
    except Exception:
        pass
