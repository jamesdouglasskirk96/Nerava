"""add verified_visits table and merchant short_code

Revision ID: 053_add_verified_visits
Revises: 052_add_claim_sessions_table
Create Date: 2026-01-24 00:00:00.000000

Adds verified_visits table for tracking driver visits with incremental verification codes.
Also adds short_code and region_code to merchants table for generating codes.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '053_add_verified_visits'
down_revision = '052_add_claim_sessions_table'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, bind) -> bool:
    """Check if a column exists in a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _table_exists(table_name: str, bind) -> bool:
    """Check if a table exists"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    """Check if an index exists on a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    """Add verified_visits table and merchant short_code fields"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()

    # UUID type - use String(36) for SQLite, UUID for PostgreSQL
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.String()

    # Add short_code and region_code to merchants table (idempotent)
    if not _column_exists('merchants', 'short_code', bind):
        with op.batch_alter_table('merchants', schema=None) as batch_op:
            batch_op.add_column(sa.Column('short_code', sa.String(16), nullable=True))

    if not _column_exists('merchants', 'region_code', bind):
        with op.batch_alter_table('merchants', schema=None) as batch_op:
            batch_op.add_column(sa.Column('region_code', sa.String(8), nullable=True, server_default='ATX'))

    if not _index_exists('merchants', 'ix_merchants_short_code', bind):
        op.create_index('ix_merchants_short_code', 'merchants', ['short_code'], unique=True)

    # Create verified_visits table (skip if exists)
    if not _table_exists('verified_visits', bind):
        op.create_table(
            'verified_visits',
            sa.Column('id', uuid_type, primary_key=True),
            sa.Column('verification_code', sa.String(32), unique=True, nullable=False),
            sa.Column('region_code', sa.String(8), nullable=False),
            sa.Column('merchant_code', sa.String(16), nullable=False),
            sa.Column('visit_number', sa.Integer(), nullable=False),
            sa.Column('merchant_id', sa.String(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False),
            sa.Column('exclusive_session_id', uuid_type, nullable=True),
            sa.Column('charger_id', sa.String(), nullable=True),
            sa.Column('verified_at', datetime_type, nullable=False, server_default=sa.func.now()),
            sa.Column('created_at', datetime_type, nullable=False, server_default=sa.func.now()),
            sa.Column('redeemed_at', datetime_type, nullable=True),
            sa.Column('order_reference', sa.String(128), nullable=True),
            sa.Column('redemption_notes', sa.String(512), nullable=True),
            sa.Column('verification_lat', sa.Float(), nullable=True),
            sa.Column('verification_lng', sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['exclusive_session_id'], ['exclusive_sessions.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ondelete='SET NULL'),
        )

    # Create indexes (skip if exist)
    indexes_to_create = [
        ('ix_verified_visits_verification_code', ['verification_code'], True),
        ('ix_verified_visits_region_code', ['region_code'], False),
        ('ix_verified_visits_merchant_code', ['merchant_code'], False),
        ('ix_verified_visits_merchant_id', ['merchant_id'], False),
        ('ix_verified_visits_driver_id', ['driver_id'], False),
        ('ix_verified_visits_exclusive_session_id', ['exclusive_session_id'], False),
        ('ix_verified_visits_charger_id', ['charger_id'], False),
        ('uq_verified_visits_merchant_visit', ['merchant_id', 'visit_number'], True),
        ('ix_verified_visits_merchant_verified', ['merchant_id', 'verified_at'], False),
        ('ix_verified_visits_driver_verified', ['driver_id', 'verified_at'], False),
    ]
    for idx_name, columns, is_unique in indexes_to_create:
        if not _index_exists('verified_visits', idx_name, bind):
            op.create_index(idx_name, 'verified_visits', columns, unique=is_unique)

    # Set initial short_codes for known merchants
    # Only set ASADAS code for the primary Asadas Grill merchant (first match)
    # Using LIMIT 1 to avoid unique constraint violations on multiple matches
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.execute("""
            UPDATE merchants
            SET short_code = 'ASADAS', region_code = 'ATX'
            WHERE id = (
                SELECT id FROM merchants
                WHERE name LIKE '%Asadas%' OR name LIKE '%asadas%'
                LIMIT 1
            )
        """)
    else:
        # PostgreSQL syntax
        op.execute("""
            UPDATE merchants
            SET short_code = 'ASADAS', region_code = 'ATX'
            WHERE id = (
                SELECT id FROM merchants
                WHERE name ILIKE '%Asadas%'
                LIMIT 1
            )
        """)


def downgrade() -> None:
    """Remove verified_visits table and merchant short_code fields"""
    # Drop indexes
    op.drop_index('ix_verified_visits_driver_verified', table_name='verified_visits')
    op.drop_index('ix_verified_visits_merchant_verified', table_name='verified_visits')
    op.drop_index('uq_verified_visits_merchant_visit', table_name='verified_visits')
    op.drop_index('ix_verified_visits_charger_id', table_name='verified_visits')
    op.drop_index('ix_verified_visits_exclusive_session_id', table_name='verified_visits')
    op.drop_index('ix_verified_visits_driver_id', table_name='verified_visits')
    op.drop_index('ix_verified_visits_merchant_id', table_name='verified_visits')
    op.drop_index('ix_verified_visits_merchant_code', table_name='verified_visits')
    op.drop_index('ix_verified_visits_region_code', table_name='verified_visits')
    op.drop_index('ix_verified_visits_verification_code', table_name='verified_visits')

    # Drop table
    op.drop_table('verified_visits')

    # Remove merchant columns
    with op.batch_alter_table('merchants', schema=None) as batch_op:
        batch_op.drop_index('ix_merchants_short_code')
        batch_op.drop_column('region_code')
        batch_op.drop_column('short_code')
