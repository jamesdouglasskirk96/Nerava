"""add nova transaction idempotency key

Revision ID: 030_nova_transaction_idempotency
Revises: 029_stripe_webhook_events
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '030_nova_transaction_idempotency'
down_revision = '029_stripe_webhook_events'
branch_labels = None
depends_on = None


def upgrade():
    # Add idempotency_key column to nova_transactions table
    op.add_column('nova_transactions', sa.Column('idempotency_key', sa.String(), nullable=True))
    
    # Create index on idempotency_key for fast lookups
    op.create_index('ix_nova_transactions_idempotency_key', 'nova_transactions', ['idempotency_key'])


def downgrade():
    op.drop_index('ix_nova_transactions_idempotency_key', table_name='nova_transactions')
    op.drop_column('nova_transactions', 'idempotency_key')

