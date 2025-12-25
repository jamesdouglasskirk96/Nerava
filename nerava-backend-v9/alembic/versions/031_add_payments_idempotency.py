"""add payments idempotency key

Revision ID: 031_payments_idempotency
Revises: 030_nova_transaction_idempotency
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '031_payments_idempotency'
down_revision = '030_nova_transaction_idempotency'
branch_labels = None
depends_on = None


def upgrade():
    # Check if payments table exists (may not exist in all deployments)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'payments' in tables:
        # Add idempotency_key column to payments table
        try:
            op.add_column('payments', sa.Column('idempotency_key', sa.String(), nullable=True))
        except Exception:
            # Column may already exist
            pass
        
        # Create index on idempotency_key for fast lookups
        try:
            op.create_index('ix_payments_idempotency_key', 'payments', ['idempotency_key'])
        except Exception:
            # Index may already exist
            pass


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'payments' in tables:
        try:
            op.drop_index('ix_payments_idempotency_key', table_name='payments')
        except Exception:
            pass
        try:
            op.drop_column('payments', 'idempotency_key')
        except Exception:
            pass


