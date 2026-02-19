#!/usr/bin/env python3
"""
Fix alembic version table for migrations that were renamed or tables that already exist.

This script detects the actual database state and stamps to the correct version
so migrations can run properly.
"""
import os
import sys

sys.path.insert(0, '/app')

def _ensure_tesla_tables(conn):
    """Create tesla_connections and ev_verification_codes tables if missing."""
    from sqlalchemy import text as sql_text
    try:
        result = conn.execute(sql_text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'tesla_connections'
            )
        """))
        if not result.scalar():
            print("Creating tesla_connections table...")
            conn.execute(sql_text("""
                CREATE TABLE tesla_connections (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    token_expires_at TIMESTAMP NOT NULL,
                    tesla_user_id VARCHAR(100),
                    vehicle_id VARCHAR(100),
                    vin VARCHAR(17),
                    vehicle_name VARCHAR(100),
                    vehicle_model VARCHAR(50),
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP,
                    last_used_at TIMESTAMP
                )
            """))
            conn.execute(sql_text("CREATE INDEX idx_tesla_connection_user ON tesla_connections(user_id)"))
            conn.execute(sql_text("CREATE INDEX idx_tesla_connection_vehicle ON tesla_connections(vehicle_id)"))
            conn.commit()
            print("tesla_connections table created")
        else:
            print("tesla_connections table already exists")

        result = conn.execute(sql_text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'ev_verification_codes'
            )
        """))
        if not result.scalar():
            print("Creating ev_verification_codes table...")
            conn.execute(sql_text("""
                CREATE TABLE ev_verification_codes (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    tesla_connection_id VARCHAR(36) REFERENCES tesla_connections(id),
                    code VARCHAR(10) UNIQUE NOT NULL,
                    charger_id VARCHAR(100),
                    merchant_place_id VARCHAR(255),
                    merchant_name VARCHAR(255),
                    charging_verified BOOLEAN NOT NULL DEFAULT false,
                    battery_level INTEGER,
                    charge_rate_kw INTEGER,
                    lat VARCHAR(20),
                    lng VARCHAR(20),
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP NOT NULL DEFAULT now(),
                    expires_at TIMESTAMP NOT NULL,
                    redeemed_at TIMESTAMP
                )
            """))
            conn.execute(sql_text("CREATE INDEX idx_ev_code ON ev_verification_codes(code)"))
            conn.execute(sql_text("CREATE INDEX idx_ev_code_user_status ON ev_verification_codes(user_id, status)"))
            conn.commit()
            print("ev_verification_codes table created")
        else:
            print("ev_verification_codes table already exists")
    except Exception as e:
        print(f"Error ensuring tesla tables: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fix alembic version by detecting actual database state."""
    from sqlalchemy import create_engine, text

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set, skipping alembic version fix")
        return 0

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            if not result.scalar():
                print("alembic_version table does not exist, nothing to fix")
                return 0

            # Get current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            if not row:
                print("No version in alembic_version table, nothing to fix")
                return 0

            current_version = row[0]
            print(f"Current alembic version: {current_version}")

            # Fix known renames - including incorrectly stamped versions
            renames = {
                '049_add_merchant_details_fields': '049_add_primary_merchant_override',
                # Fix versions that were incorrectly stamped with full filenames
                '069_add_merchant_geofence_radius': '069',
                '068_add_car_pins_table': '068',
                '067_add_phone_session_token': '067',
                '066_add_arrival_code_fields': '066',
                '065_add_virtual_keys_table': '065',
                '064_add_queued_order_fields': '064',
                '063_add_queued_orders_table': '063',
                '062_add_ev_arrival_tables': '062',
                '061_add_admin_role_to_users': '061',
                '060_add_consent_fields': '060',
                '059_add_user_consents_table': '059',
            }
            if current_version in renames:
                new_version = renames[current_version]
                print(f"Renaming {current_version} -> {new_version}")
                conn.execute(text(
                    "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
                ), {"old": current_version, "new": new_version})
                conn.commit()
                current_version = new_version
                print(f"Updated to {current_version}")

            # Detect actual database state by checking key markers
            markers = {}

            # Check for tables
            for table in ['favorite_merchants', 'claim_sessions', 'verified_visits',
                         'amenity_votes', 'user_consents', 'arrival_sessions',
                         'queued_orders', 'virtual_keys', 'car_pins']:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    )
                """))
                markers[f'table:{table}'] = result.scalar()

            # Check for key columns
            col_checks = [
                ('merchants', 'short_code'),
                ('merchants', 'ordering_url'),
                ('merchants', 'geofence_radius_m'),
                ('users', 'admin_role'),
                ('users', 'vehicle_color'),
                ('arrival_sessions', 'flow_type') if markers.get('table:arrival_sessions') else None,
                ('arrival_sessions', 'phone_session_token') if markers.get('table:arrival_sessions') else None,
            ]
            for check in col_checks:
                if check is None:
                    continue
                table, col = check
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{col}'
                    )
                """))
                markers[f'col:{table}.{col}'] = result.scalar()

            print(f"Database state markers: {markers}")

            # Determine the correct version based on markers
            # Migration order with their key markers:
            # 051: table:favorite_merchants
            # 052: table:claim_sessions
            # 053: table:verified_visits, col:merchants.short_code
            # 055: table:amenity_votes
            # 059: table:user_consents
            # 061: col:users.admin_role
            # 062: table:arrival_sessions, col:merchants.ordering_url
            # 063: table:queued_orders
            # 065: table:virtual_keys
            # 066: col:arrival_sessions.flow_type
            # 067: col:arrival_sessions.phone_session_token
            # 068: table:car_pins
            # 069: col:merchants.geofence_radius_m

            target_version = current_version

            # Work backwards from latest to find the right version
            # NOTE: Revision IDs must match exactly what's in the migration files
            if markers.get('col:merchants.geofence_radius_m'):
                target_version = '069'
            elif markers.get('table:car_pins'):
                target_version = '068'
            elif markers.get('col:arrival_sessions.phone_session_token'):
                target_version = '067'
            elif markers.get('col:arrival_sessions.flow_type'):
                target_version = '066'
            elif markers.get('table:virtual_keys'):
                target_version = '065'
            elif markers.get('table:queued_orders'):
                target_version = '064'  # 064 adds queued order fields
            elif markers.get('table:arrival_sessions') or markers.get('col:merchants.ordering_url'):
                target_version = '062'
            elif markers.get('col:users.admin_role'):
                target_version = '061'
            elif markers.get('table:user_consents'):
                target_version = '060'
            elif markers.get('table:amenity_votes'):
                target_version = '055'
            elif markers.get('table:verified_visits') or markers.get('col:merchants.short_code'):
                target_version = '053'
            elif markers.get('table:claim_sessions'):
                target_version = '052'
            elif markers.get('table:favorite_merchants'):
                target_version = '051'

            print(f"Detected target version: {target_version}")

            if target_version != current_version:
                print(f"Stamping database from {current_version} to {target_version}")
                conn.execute(text(
                    "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
                ), {"old": current_version, "new": target_version})
                conn.commit()
                print(f"Successfully stamped to {target_version}")
            else:
                print(f"Version already correct at {current_version}")

            # Create missing tables that migrations may have skipped
            _ensure_tesla_tables(conn)

            return 0
    except Exception as e:
        print(f"Error fixing alembic version: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    sys.exit(main())
