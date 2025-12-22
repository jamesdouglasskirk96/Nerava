"""make idempotency keys unique

Revision ID: 033_make_idempotency_keys_unique
Revises: 032_vehicle_token_encryption
Create Date: 2024-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '033_make_idempotency_keys_unique'
down_revision = '032_vehicle_token_encryption'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Cleanup duplicate idempotency keys (non-destructive)
    # Keep earliest row, set others to NULL
    
    # Payments table
    if 'payments' in tables:
        print("Cleaning up duplicate idempotency keys in payments table...")
        
        # Find duplicate groups
        duplicates_result = bind.execute(text("""
            SELECT idempotency_key, COUNT(*) as cnt, MIN(id) as first_id
            FROM payments
            WHERE idempotency_key IS NOT NULL
            GROUP BY idempotency_key
            HAVING COUNT(*) > 1
        """))
        duplicates = duplicates_result.fetchall()
        
        duplicate_groups = len(duplicates)
        rows_normalized = 0
        
        for dup in duplicates:
            idempotency_key = dup[0]
            first_id = dup[2]
            
            # Set idempotency_key to NULL for all rows except the first one
            result = bind.execute(text("""
                UPDATE payments
                SET idempotency_key = NULL
                WHERE idempotency_key = :key AND id != :first_id
            """), {"key": idempotency_key, "first_id": first_id})
            rows_normalized += result.rowcount
        
        print(f"payments: {duplicate_groups} duplicate key groups, {rows_normalized} rows normalized")
        
        # Add uniqueness constraint
        try:
            if is_postgres:
                # Postgres: partial unique index (NULLs allowed multiple)
                op.create_index(
                    'uq_payments_idempotency_key',
                    'payments',
                    ['idempotency_key'],
                    unique=True,
                    postgresql_where=sa.text('idempotency_key IS NOT NULL')
                )
            else:
                # SQLite: unique index (NULLs allowed multiple)
                op.create_index(
                    'uq_payments_idempotency_key',
                    'payments',
                    ['idempotency_key'],
                    unique=True
                )
        except Exception as e:
            print(f"Warning: Could not create unique index on payments.idempotency_key: {e}")
    
    # Nova transactions table
    if 'nova_transactions' in tables:
        print("Cleaning up duplicate idempotency keys in nova_transactions table...")
        
        # Find duplicate groups
        duplicates_result = bind.execute(text("""
            SELECT idempotency_key, COUNT(*) as cnt, MIN(id) as first_id
            FROM nova_transactions
            WHERE idempotency_key IS NOT NULL
            GROUP BY idempotency_key
            HAVING COUNT(*) > 1
        """))
        duplicates = duplicates_result.fetchall()
        
        duplicate_groups = len(duplicates)
        rows_normalized = 0
        
        for dup in duplicates:
            idempotency_key = dup[0]
            first_id = dup[2]
            
            # Set idempotency_key to NULL for all rows except the first one
            result = bind.execute(text("""
                UPDATE nova_transactions
                SET idempotency_key = NULL
                WHERE idempotency_key = :key AND id != :first_id
            """), {"key": idempotency_key, "first_id": first_id})
            rows_normalized += result.rowcount
        
        print(f"nova_transactions: {duplicate_groups} duplicate key groups, {rows_normalized} rows normalized")
        
        # Add uniqueness constraint
        try:
            if is_postgres:
                # Postgres: partial unique index
                op.create_index(
                    'uq_nova_transactions_idempotency_key',
                    'nova_transactions',
                    ['idempotency_key'],
                    unique=True,
                    postgresql_where=sa.text('idempotency_key IS NOT NULL')
                )
            else:
                # SQLite: unique index
                op.create_index(
                    'uq_nova_transactions_idempotency_key',
                    'nova_transactions',
                    ['idempotency_key'],
                    unique=True
                )
        except Exception as e:
            print(f"Warning: Could not create unique index on nova_transactions.idempotency_key: {e}")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    # Drop unique indexes
    if 'payments' in tables:
        try:
            op.drop_index('uq_payments_idempotency_key', table_name='payments')
        except Exception:
            pass
    
    if 'nova_transactions' in tables:
        try:
            op.drop_index('uq_nova_transactions_idempotency_key', table_name='nova_transactions')
        except Exception:
            pass

