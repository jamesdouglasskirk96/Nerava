"""Add EnergyEvent and Zone tables for data-scoped charge parties

Revision ID: 019
Revises: 018
Create Date: 2025-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    # 1. Create zones table
    if not _has_table('zones'):
        op.create_table(
            'zones',
            sa.Column('slug', sa.String(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('center_lat', sa.Float(), nullable=False),
            sa.Column('center_lng', sa.Float(), nullable=False),
            sa.Column('radius_m', sa.Integer(), nullable=False, server_default='1000'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
        
        # Seed domain_austin zone
        op.execute("""
            INSERT INTO zones (slug, name, center_lat, center_lng, radius_m)
            VALUES ('domain_austin', 'The Domain, Austin', 30.4021, -97.7266, 1000)
            ON CONFLICT DO NOTHING
        """)
    
    # 2. Create energy_events table
    if not _has_table('energy_events'):
        op.create_table(
            'energy_events',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('slug', sa.String(), nullable=False, unique=True),
            sa.Column('zone_slug', sa.String(), sa.ForeignKey('zones.slug'), nullable=False, index=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('starts_at', sa.DateTime(), nullable=False),
            sa.Column('ends_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='draft', index=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
        
        op.create_index('ix_energy_events_zone_status', 'energy_events', ['zone_slug', 'status'])
        
        # Seed domain_jan_2025 event
        op.execute("""
            INSERT INTO energy_events (id, slug, zone_slug, name, starts_at, status)
            VALUES (
                'evt_domain_jan_2025',
                'domain_jan_2025',
                'domain_austin',
                'Domain Charge Party - January 2025',
                datetime('now'),
                'active'
            )
            ON CONFLICT DO NOTHING
        """)
    
    # 3. Update domain_merchants to use zone_slug instead of domain_zone
    if _has_table('domain_merchants'):
        # Add zone_slug if it doesn't exist
        try:
            bind = op.get_bind()
            insp = sa.inspect(bind)
            columns = [col['name'] for col in insp.get_columns('domain_merchants')]
            
            if 'zone_slug' not in columns:
                # If domain_zone exists, migrate data
                if 'domain_zone' in columns:
                    op.execute("""
                        ALTER TABLE domain_merchants 
                        ADD COLUMN zone_slug TEXT;
                        UPDATE domain_merchants 
                        SET zone_slug = domain_zone 
                        WHERE domain_zone IS NOT NULL;
                        UPDATE domain_merchants 
                        SET zone_slug = 'domain_austin' 
                        WHERE zone_slug IS NULL;
                    """)
                else:
                    op.add_column('domain_merchants', sa.Column('zone_slug', sa.String(), nullable=False, server_default='domain_austin'))
                
                # Update index
                op.drop_index('ix_domain_merchants_domain_zone_status', table_name='domain_merchants', if_exists=True)
                op.create_index('ix_domain_merchants_zone_status', 'domain_merchants', ['zone_slug', 'status'])
        except Exception:
            pass  # Column might already exist
    
    # 4. Add event_id to domain_charging_sessions and nova_transactions
    if _has_table('domain_charging_sessions'):
        try:
            bind = op.get_bind()
            insp = sa.inspect(bind)
            columns = [col['name'] for col in insp.get_columns('domain_charging_sessions')]
            if 'event_id' not in columns:
                op.add_column('domain_charging_sessions', sa.Column('event_id', sa.String(), sa.ForeignKey('energy_events.id'), nullable=True))
                op.create_index('ix_domain_charging_sessions_event_id', 'domain_charging_sessions', ['event_id'])
        except Exception:
            pass
    
    if _has_table('nova_transactions'):
        try:
            bind = op.get_bind()
            insp = sa.inspect(bind)
            columns = [col['name'] for col in insp.get_columns('nova_transactions')]
            if 'event_id' not in columns:
                op.add_column('nova_transactions', sa.Column('event_id', sa.String(), sa.ForeignKey('energy_events.id'), nullable=True))
                op.create_index('ix_nova_transactions_event_id', 'nova_transactions', ['event_id'])
        except Exception:
            pass


def downgrade() -> None:
    if _has_table('nova_transactions'):
        op.drop_index('ix_nova_transactions_event_id', table_name='nova_transactions', if_exists=True)
        op.drop_column('nova_transactions', 'event_id')
    
    if _has_table('domain_charging_sessions'):
        op.drop_index('ix_domain_charging_sessions_event_id', table_name='domain_charging_sessions', if_exists=True)
        op.drop_column('domain_charging_sessions', 'event_id')
    
    if _has_table('energy_events'):
        op.drop_table('energy_events')
    
    if _has_table('zones'):
        op.drop_table('zones')

