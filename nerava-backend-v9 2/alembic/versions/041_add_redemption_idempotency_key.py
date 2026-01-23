"""add redemption idempotency key

Revision ID: 041_add_redemption_idempotency_key
Revises: 040_add_wallet_balance_constraint
Create Date: 2025-01-27 12:00:00.000000

P1-F Security: Adds idempotency_key to merchant_redemptions table to prevent
replay attacks on non-Square QR redemptions. Square redemptions already have
unique constraint on (merchant_id, square_order_id), but manual redemptions
need idempotency protection.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '041_add_redemption_idempotency_key'
down_revision = '040_add_wallet_balance_constraint'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    """Check if a table exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        columns = insp.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
        return False


def _has_constraint(table_name: str, constraint_name: str) -> bool:
    """Check if a unique constraint exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        constraints = insp.get_unique_constraints(table_name)
        return any(c['name'] == constraint_name for c in constraints)
    except Exception:
        return False


def upgrade():
    """Add idempotency_key column and unique constraint to merchant_redemptions"""
    
    if _has_table('merchant_redemptions'):
        # Add idempotency_key column (nullable for backward compatibility with existing records)
        if not _has_column('merchant_redemptions', 'idempotency_key'):
            op.add_column('merchant_redemptions', sa.Column('idempotency_key', sa.String(), nullable=True))
            
            # Add index for idempotency_key lookups
            op.create_index('ix_merchant_redemptions_idempotency_key', 'merchant_redemptions', ['idempotency_key'])
        
        # Add unique constraint on (merchant_id, idempotency_key)
        # Note: This allows NULL idempotency_key for existing records, but requires uniqueness for non-NULL values
        if not _has_constraint('merchant_redemptions', 'uq_merchant_idempotency'):
            # For SQLite: Use a unique index instead of constraint (handles NULLs better)
            bind = op.get_bind()
            dialect_name = bind.dialect.name
            
            if dialect_name == 'sqlite':
                # SQLite: Create unique index
                # Note: SQLite allows multiple NULLs in unique indexes by default
                # So this will enforce uniqueness on non-NULL idempotency_key values
                op.execute(sa.text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_merchant_idempotency 
                    ON merchant_redemptions(merchant_id, idempotency_key)
                """))
            else:
                # PostgreSQL: Create unique constraint with NULLS NOT DISTINCT or partial index
                # For PostgreSQL 15+, we can use NULLS NOT DISTINCT
                # For older versions, we'll use a partial unique index
                try:
                    op.create_unique_constraint(
                        'uq_merchant_idempotency',
                        'merchant_redemptions',
                        ['merchant_id', 'idempotency_key']
                    )
                except Exception:
                    # If constraint creation fails (e.g., due to NULL handling), use unique index
                    # PostgreSQL 15+ supports NULLS NOT DISTINCT, older versions need partial index
                    # For now, use unique index which allows NULLs (like SQLite)
                    op.execute(sa.text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_merchant_idempotency 
                        ON merchant_redemptions(merchant_id, idempotency_key)
                    """))


def downgrade():
    """Remove idempotency_key column and unique constraint from merchant_redemptions"""
    
    if _has_table('merchant_redemptions'):
        # Drop unique constraint/index
        bind = op.get_bind()
        dialect_name = bind.dialect.name
        
        if dialect_name == 'sqlite':
            op.execute(sa.text("DROP INDEX IF EXISTS uq_merchant_idempotency"))
        else:
            try:
                if _has_constraint('merchant_redemptions', 'uq_merchant_idempotency'):
                    op.drop_constraint('uq_merchant_idempotency', 'merchant_redemptions', type_='unique')
            except Exception:
                op.execute(sa.text("DROP INDEX IF EXISTS uq_merchant_idempotency"))
        
        # Drop index for idempotency_key
        try:
            op.drop_index('ix_merchant_redemptions_idempotency_key', table_name='merchant_redemptions')
        except Exception:
            pass
        
        # Drop column
        if _has_column('merchant_redemptions', 'idempotency_key'):
            op.drop_column('merchant_redemptions', 'idempotency_key')

