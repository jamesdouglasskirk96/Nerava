"""payments state machine

Revision ID: 036_payments_state_machine
Revises: 035_vehicle_tokens_default_encrypted
Create Date: 2024-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '036_payments_state_machine'
down_revision = '035_vehicle_tokens_default_encrypted'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Payments table: add state machine columns
    if 'payments' in tables:
        columns = [col['name'] for col in inspector.get_columns('payments')]
        
        # Add status column if missing (check-before-add)
        if 'status' not in columns:
            op.add_column('payments', sa.Column('status', sa.String(), nullable=True))
            # Normalize old statuses: 'paid' → 'succeeded'
            bind.execute(text("""
                UPDATE payments SET status = 'succeeded' WHERE status = 'paid'
            """))
            # Set default for NULL
            bind.execute(text("""
                UPDATE payments SET status = 'pending' WHERE status IS NULL
            """))
            # Now make it NOT NULL with default
            op.alter_column('payments', 'status',
                          nullable=False,
                          server_default='pending',
                          existing_type=sa.String())
        
        # Add payload_hash column if missing
        if 'payload_hash' not in columns:
            op.add_column('payments', sa.Column('payload_hash', sa.String(), nullable=True))
        
        # Add stripe_transfer_id column if missing
        if 'stripe_transfer_id' not in columns:
            op.add_column('payments', sa.Column('stripe_transfer_id', sa.String(), nullable=True))
        
        # Add stripe_status column if missing
        if 'stripe_status' not in columns:
            op.add_column('payments', sa.Column('stripe_status', sa.String(), nullable=True))
        
        # Add error_code column if missing
        if 'error_code' not in columns:
            op.add_column('payments', sa.Column('error_code', sa.String(), nullable=True))
        
        # Add error_message column if missing
        if 'error_message' not in columns:
            op.add_column('payments', sa.Column('error_message', sa.Text(), nullable=True))
        
        # Add reconciled_at column if missing
        if 'reconciled_at' not in columns:
            op.add_column('payments', sa.Column('reconciled_at', sa.DateTime(), nullable=True))
        
        # Add no_transfer_confirmed column if missing
        if 'no_transfer_confirmed' not in columns:
            op.add_column('payments', sa.Column('no_transfer_confirmed', sa.Boolean(), nullable=False, server_default='0'))
    
    # Nova transactions table: add payload_hash column
    if 'nova_transactions' in tables:
        columns = [col['name'] for col in inspector.get_columns('nova_transactions')]
        
        if 'payload_hash' not in columns:
            op.add_column('nova_transactions', sa.Column('payload_hash', sa.String(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    # Remove columns from payments
    if 'payments' in tables:
        columns = [col['name'] for col in inspector.get_columns('payments')]
        
        if 'no_transfer_confirmed' in columns:
            op.drop_column('payments', 'no_transfer_confirmed')
        if 'reconciled_at' in columns:
            op.drop_column('payments', 'reconciled_at')
        if 'error_message' in columns:
            op.drop_column('payments', 'error_message')
        if 'error_code' in columns:
            op.drop_column('payments', 'error_code')
        if 'stripe_status' in columns:
            op.drop_column('payments', 'stripe_status')
        if 'stripe_transfer_id' in columns:
            op.drop_column('payments', 'stripe_transfer_id')
        if 'payload_hash' in columns:
            op.drop_column('payments', 'payload_hash')
        # Note: status column kept (may have data)
    
    # Remove payload_hash from nova_transactions
    if 'nova_transactions' in tables:
        columns = [col['name'] for col in inspector.get_columns('nova_transactions')]
        if 'payload_hash' in columns:
            op.drop_column('nova_transactions', 'payload_hash')

