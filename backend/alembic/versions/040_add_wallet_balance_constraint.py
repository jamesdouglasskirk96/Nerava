"""add wallet balance constraint

Revision ID: 040_add_wallet_balance_constraint
Revises: 039_add_client_events
Create Date: 2025-01-27 12:00:00.000000

P0-D Security: Adds CheckConstraint to prevent negative wallet balances at DB level.
This ensures even if application code has bugs or race conditions, the database
will enforce non-negative balances.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040_add_wallet_balance_constraint'
down_revision = '039_add_client_events'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    """Check if a table exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_constraint(table_name: str, constraint_name: str) -> bool:
    """Check if a constraint exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        constraints = insp.get_check_constraints(table_name)
        return any(c['name'] == constraint_name for c in constraints)
    except Exception:
        return False


def upgrade():
    """Add CheckConstraint on driver_wallets.nova_balance >= 0"""
    
    if _has_table('driver_wallets'):
        # Fix any existing negative balances first (set to 0)
        bind = op.get_bind()
        bind.execute(sa.text("UPDATE driver_wallets SET nova_balance = 0 WHERE nova_balance < 0"))
        
        # Add check constraint
        if not _has_constraint('driver_wallets', 'ck_wallet_nova_balance_nonneg'):
            # SQLite doesn't support ALTER TABLE ADD CONSTRAINT directly
            # We need to use a different approach
            bind = op.get_bind()
            dialect_name = bind.dialect.name
            
            if dialect_name == 'sqlite':
                # SQLite: Need to recreate table with constraint
                # This is more complex, so we'll use a pragma check for SQLite
                # For SQLite, we'll add a trigger instead which is simpler
                op.execute(sa.text("""
                    CREATE TRIGGER IF NOT EXISTS check_nova_balance_nonneg
                    BEFORE UPDATE ON driver_wallets
                    FOR EACH ROW
                    WHEN NEW.nova_balance < 0
                    BEGIN
                        SELECT RAISE(ABORT, 'nova_balance cannot be negative');
                    END
                """))
                
                op.execute(sa.text("""
                    CREATE TRIGGER IF NOT EXISTS check_nova_balance_nonneg_insert
                    BEFORE INSERT ON driver_wallets
                    FOR EACH ROW
                    WHEN NEW.nova_balance < 0
                    BEGIN
                        SELECT RAISE(ABORT, 'nova_balance cannot be negative');
                    END
                """))
            else:
                # PostgreSQL and others: Use CHECK constraint
                op.create_check_constraint(
                    'ck_wallet_nova_balance_nonneg',
                    'driver_wallets',
                    'nova_balance >= 0'
                )


def downgrade():
    """Remove CheckConstraint on driver_wallets.nova_balance"""
    
    if _has_table('driver_wallets'):
        bind = op.get_bind()
        dialect_name = bind.dialect.name
        
        if dialect_name == 'sqlite':
            # SQLite: Drop triggers
            op.execute(sa.text("DROP TRIGGER IF EXISTS check_nova_balance_nonneg"))
            op.execute(sa.text("DROP TRIGGER IF EXISTS check_nova_balance_nonneg_insert"))
        else:
            # PostgreSQL and others: Drop constraint
            if _has_constraint('driver_wallets', 'ck_wallet_nova_balance_nonneg'):
                op.drop_constraint('ck_wallet_nova_balance_nonneg', 'driver_wallets', type_='check')








