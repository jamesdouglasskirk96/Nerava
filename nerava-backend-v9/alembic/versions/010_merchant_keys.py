"""Add merchant API keys and dashboard fields

Revision ID: 010_merchant_keys
Revises: 009
Create Date: 2025-10-29 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "010_merchant_keys"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    # Add merchant dashboard fields (idempotent)
    try:
        op.add_column('merchants', sa.Column('slug', sa.String(200), nullable=True))
        op.add_column('merchants', sa.Column('owner_email', sa.String(200), nullable=True))
        op.add_column('merchants', sa.Column('api_key', sa.String(200), nullable=True))
        op.create_unique_constraint('uq_merchants_slug', 'merchants', ['slug'])
        op.create_index('idx_merchants_api_key', 'merchants', ['api_key'])
    except Exception:
        pass


def downgrade():
    try:
        op.drop_index('idx_merchants_api_key', 'merchants')
        op.drop_constraint('uq_merchants_slug', 'merchants')
        op.drop_column('merchants', 'api_key')
        op.drop_column('merchants', 'owner_email')
        op.drop_column('merchants', 'slug')
    except Exception:
        pass

