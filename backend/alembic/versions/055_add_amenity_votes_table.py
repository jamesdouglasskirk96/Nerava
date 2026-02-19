"""add amenity votes table

Revision ID: 055_add_amenity_votes_table
Revises: 054
Create Date: 2026-01-27 16:00:00.000000

Adds amenity_votes table for user amenity voting functionality
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '055_add_amenity_votes_table'
down_revision = '054'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add amenity_votes table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()
    
    # Create amenity_votes table
    op.create_table(
        'amenity_votes',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amenity', sa.String(20), nullable=False),  # 'bathroom' or 'wifi'
        sa.Column('vote_type', sa.String(10), nullable=False),  # 'up' or 'down'
        sa.Column('created_at', datetime_type, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique constraint on (merchant_id, user_id, amenity)
    op.create_unique_constraint('uq_amenity_vote', 'amenity_votes', ['merchant_id', 'user_id', 'amenity'])
    
    # Create index for aggregation queries (merchant_id, amenity)
    op.create_index('idx_amenity_votes_merchant', 'amenity_votes', ['merchant_id', 'amenity'])
    
    # Create index on user_id for user queries
    op.create_index('idx_amenity_votes_user', 'amenity_votes', ['user_id'])


def downgrade() -> None:
    """Remove amenity_votes table"""
    op.drop_index('idx_amenity_votes_user', table_name='amenity_votes')
    op.drop_index('idx_amenity_votes_merchant', table_name='amenity_votes')
    op.drop_constraint('uq_amenity_vote', 'amenity_votes', type_='unique')
    op.drop_table('amenity_votes')
