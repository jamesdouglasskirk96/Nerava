"""Add Stripe Connect fields to users and payments

Revision ID: 007
Revises: 006
Create Date: 2025-10-29 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add Stripe fields to users table
    try:
        op.add_column('users', sa.Column('stripe_account_id', sa.String(200), nullable=True))
        op.add_column('users', sa.Column('stripe_onboarded', sa.Boolean(), nullable=True, server_default='0'))
        op.create_index('idx_users_stripe_account', 'users', ['stripe_account_id'])
    except Exception:
        # Columns might already exist
        pass
    
    # Add client_token to payments table (for idempotency)
    try:
        op.add_column('payments', sa.Column('client_token', sa.String(200), nullable=True))
        op.create_index('idx_payments_client_token', 'payments', ['client_token'])
    except Exception:
        # Column might already exist
        pass


def downgrade():
    try:
        op.drop_index('idx_payments_client_token', 'payments')
        op.drop_column('payments', 'client_token')
        op.drop_index('idx_users_stripe_account', 'users')
        op.drop_column('users', 'stripe_onboarded')
        op.drop_column('users', 'stripe_account_id')
    except Exception:
        pass

