"""add vehicle token encryption version

Revision ID: 032_vehicle_token_encryption
Revises: 031_payments_idempotency
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '032_vehicle_token_encryption'
down_revision = '031_payments_idempotency'
branch_labels = None
depends_on = None


def upgrade():
    # Add encryption_version column to vehicle_tokens table
    # Default to 0 (plaintext) for existing tokens, new tokens will use 1 (encrypted)
    op.add_column('vehicle_tokens', sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('vehicle_tokens', 'encryption_version')


