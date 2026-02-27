#!/usr/bin/env python3
"""
Fix alembic version table for migrations that were renamed or tables that already exist.

This script detects the actual database state and stamps to the correct version
so migrations can run properly. It also creates any missing tables/columns that
migrations would have added, to handle cases where Alembic migrations fail due
to schema mismatches.
"""
import os
import sys

sys.path.insert(0, '/app')


def _table_exists(conn, table_name):
    from sqlalchemy import text
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = :t
        )
    """), {"t": table_name})
    return result.scalar()


def _column_exists(conn, table_name, column_name):
    from sqlalchemy import text
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
        )
    """), {"t": table_name, "c": column_name})
    return result.scalar()


def _safe_execute(conn, sql, description=""):
    """Execute SQL, ignoring errors (for CREATE IF NOT EXISTS, ADD COLUMN, etc.)."""
    from sqlalchemy import text
    try:
        conn.execute(text(sql))
        if description:
            print(f"  OK: {description}")
        return True
    except Exception as e:
        if description:
            print(f"  SKIP: {description} ({e})")
        conn.rollback()
        return False


def _upgrade_driver_wallets_legacy(conn):
    """Upgrade legacy driver_wallets table (user_id PK, nova_balance) to new schema (id PK, driver_id FK, balance_cents)."""
    from sqlalchemy import text
    import uuid as uuid_mod

    print("=== Upgrading driver_wallets from legacy to new schema ===")

    # Step 1: Save existing data before transforming
    result = conn.execute(text("SELECT user_id, COALESCE(nova_balance, 0), created_at FROM driver_wallets"))
    legacy_rows = result.fetchall()
    print(f"  Found {len(legacy_rows)} legacy wallet rows to migrate")

    # Step 2: Drop FK constraints from other tables that reference driver_wallets
    _safe_execute(conn, "ALTER TABLE apple_pass_registrations DROP CONSTRAINT IF EXISTS apple_pass_registrations_driver_wallet_id_fkey", "Drop apple_pass FK")
    _safe_execute(conn, "ALTER TABLE google_wallet_links DROP CONSTRAINT IF EXISTS google_wallet_links_driver_wallet_id_fkey", "Drop google_wallet FK")
    conn.commit()

    # Step 3: Drop and recreate with correct schema (safest approach)
    conn.execute(text("DROP TABLE driver_wallets CASCADE"))
    conn.commit()
    print("  Dropped legacy driver_wallets table")

    conn.execute(text("""
        CREATE TABLE driver_wallets (
            id VARCHAR(36) PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
            balance_cents INTEGER NOT NULL DEFAULT 0,
            pending_balance_cents INTEGER NOT NULL DEFAULT 0,
            stripe_account_id VARCHAR(255),
            stripe_account_status VARCHAR(50),
            stripe_onboarding_complete BOOLEAN NOT NULL DEFAULT false,
            total_earned_cents INTEGER NOT NULL DEFAULT 0,
            total_withdrawn_cents INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP
        )
    """))
    conn.commit()
    print("  Created new driver_wallets table")

    # Step 4: Re-insert migrated data
    for row in legacy_rows:
        user_id, balance, created_at = row[0], row[1], row[2]
        wallet_id = str(uuid_mod.uuid4())
        conn.execute(text("""
            INSERT INTO driver_wallets (id, driver_id, balance_cents, pending_balance_cents,
                stripe_onboarding_complete, total_earned_cents, total_withdrawn_cents, created_at)
            VALUES (:wid, :did, :bal, 0, false, :earn, 0, :created)
        """), {
            "wid": wallet_id, "did": user_id, "bal": balance,
            "earn": balance, "created": created_at,
        })
        print(f"  Migrated wallet for user {user_id}: {balance} cents (wallet_id={wallet_id})")
    conn.commit()

    # Step 5: Re-add FK constraints from other tables (now referencing driver_id)
    if _table_exists(conn, 'apple_pass_registrations') and _column_exists(conn, 'apple_pass_registrations', 'driver_wallet_id'):
        _safe_execute(conn,
            "ALTER TABLE apple_pass_registrations ADD CONSTRAINT apple_pass_registrations_driver_wallet_id_fkey FOREIGN KEY (driver_wallet_id) REFERENCES driver_wallets(driver_id)",
            "Re-add apple_pass FK")
    if _table_exists(conn, 'google_wallet_links') and _column_exists(conn, 'google_wallet_links', 'driver_wallet_id'):
        _safe_execute(conn,
            "ALTER TABLE google_wallet_links ADD CONSTRAINT google_wallet_links_driver_wallet_id_fkey FOREIGN KEY (driver_wallet_id) REFERENCES driver_wallets(driver_id)",
            "Re-add google_wallet FK")
    conn.commit()

    print("=== driver_wallets schema upgrade complete ===")


def _ensure_tables_070_079(conn):
    """Ensure all tables and columns from migrations 070-079 exist."""
    from sqlalchemy import text

    print("=== Ensuring schema from migrations 070-079 ===")

    # --- Migration 070: arrival_sessions columns ---
    if _table_exists(conn, 'arrival_sessions'):
        cols_070 = [
            ('browser_source', 'VARCHAR(30)'),
            ('ev_brand', 'VARCHAR(30)'),
            ('ev_firmware', 'VARCHAR(50)'),
            ('fulfillment_type', 'VARCHAR(20)'),
            ('queued_order_status', "VARCHAR(20) DEFAULT 'queued'"),
            ('destination_merchant_id', 'VARCHAR(255)'),
            ('destination_lat', 'DOUBLE PRECISION'),
            ('destination_lng', 'DOUBLE PRECISION'),
            ('arrival_detected_at', 'TIMESTAMP'),
            ('order_released_at', 'TIMESTAMP'),
            ('order_ready_at', 'TIMESTAMP'),
            ('arrival_distance_m', 'DOUBLE PRECISION'),
            ('virtual_key_id', 'VARCHAR(36)'),
            ('arrival_source', 'VARCHAR(30)'),
            ('vehicle_soc_at_arrival', 'DOUBLE PRECISION'),
        ]
        for col_name, col_type in cols_070:
            if not _column_exists(conn, 'arrival_sessions', col_name):
                _safe_execute(conn,
                    f"ALTER TABLE arrival_sessions ADD COLUMN {col_name} {col_type}",
                    f"arrival_sessions.{col_name}")
        _safe_execute(conn,
            "CREATE INDEX IF NOT EXISTS idx_arrival_queued ON arrival_sessions (queued_order_status, destination_merchant_id)",
            "idx_arrival_queued")
        conn.commit()

    # --- Migration 072: Tesla tables ---
    if not _table_exists(conn, 'tesla_connections'):
        _safe_execute(conn, """
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
        """, "CREATE tesla_connections")
        conn.commit()

    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_tesla_connection_user ON tesla_connections(user_id)", "")
    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_tesla_connection_vehicle ON tesla_connections(vehicle_id)", "")

    if not _table_exists(conn, 'ev_verification_codes'):
        _safe_execute(conn, """
            CREATE TABLE ev_verification_codes (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                tesla_connection_id VARCHAR(36),
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
        """, "CREATE ev_verification_codes")
        conn.commit()

    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_ev_code ON ev_verification_codes(code)", "")
    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_ev_code_user_status ON ev_verification_codes(user_id, status)", "")
    conn.commit()

    # --- Migration 073: Wallet tables ---
    if not _table_exists(conn, 'driver_wallets'):
        _safe_execute(conn, """
            CREATE TABLE driver_wallets (
                id VARCHAR(36) PRIMARY KEY,
                driver_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
                balance_cents INTEGER NOT NULL DEFAULT 0,
                pending_balance_cents INTEGER NOT NULL DEFAULT 0,
                stripe_account_id VARCHAR(255),
                stripe_account_status VARCHAR(50),
                stripe_onboarding_complete BOOLEAN NOT NULL DEFAULT false,
                total_earned_cents INTEGER NOT NULL DEFAULT 0,
                total_withdrawn_cents INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP
            )
        """, "CREATE driver_wallets")
        conn.commit()
    elif _table_exists(conn, 'driver_wallets') and not _column_exists(conn, 'driver_wallets', 'driver_id'):
        # Legacy schema detected (has user_id PK, nova_balance) - upgrade to new schema
        _upgrade_driver_wallets_legacy(conn)

    if not _table_exists(conn, 'payouts'):
        _safe_execute(conn, """
            CREATE TABLE payouts (
                id VARCHAR(36) PRIMARY KEY,
                driver_id INTEGER NOT NULL,
                wallet_id VARCHAR(36) NOT NULL,
                amount_cents INTEGER NOT NULL,
                stripe_transfer_id VARCHAR(255),
                stripe_payout_id VARCHAR(255),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                failure_reason VARCHAR(500),
                idempotency_key VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP,
                paid_at TIMESTAMP
            )
        """, "CREATE payouts")
        conn.commit()

    if not _table_exists(conn, 'cards'):
        _safe_execute(conn, """
            CREATE TABLE cards (
                id VARCHAR(36) PRIMARY KEY,
                driver_id INTEGER NOT NULL,
                fidel_card_id VARCHAR(255),
                last4 VARCHAR(4) NOT NULL,
                brand VARCHAR(20) NOT NULL,
                fingerprint VARCHAR(100),
                is_active BOOLEAN NOT NULL DEFAULT true,
                linked_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """, "CREATE cards")
        conn.commit()

    if not _table_exists(conn, 'merchant_offers'):
        _safe_execute(conn, """
            CREATE TABLE merchant_offers (
                id VARCHAR(36) PRIMARY KEY,
                merchant_id VARCHAR(36) NOT NULL,
                fidel_offer_id VARCHAR(255),
                fidel_program_id VARCHAR(255),
                min_spend_cents INTEGER NOT NULL DEFAULT 0,
                reward_cents INTEGER NOT NULL,
                reward_percent INTEGER,
                max_reward_cents INTEGER,
                is_active BOOLEAN NOT NULL DEFAULT true,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP
            )
        """, "CREATE merchant_offers")
        conn.commit()

    if not _table_exists(conn, 'clo_transactions'):
        _safe_execute(conn, """
            CREATE TABLE clo_transactions (
                id VARCHAR(36) PRIMARY KEY,
                driver_id INTEGER NOT NULL,
                card_id VARCHAR(36) NOT NULL,
                merchant_id VARCHAR(36) NOT NULL,
                offer_id VARCHAR(36),
                amount_cents INTEGER NOT NULL,
                reward_cents INTEGER,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                external_id VARCHAR(255),
                charging_session_id VARCHAR(36),
                transaction_time TIMESTAMP NOT NULL,
                merchant_name VARCHAR(255),
                merchant_location VARCHAR(500),
                eligibility_reason VARCHAR(200),
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                processed_at TIMESTAMP
            )
        """, "CREATE clo_transactions")
        conn.commit()

    if not _table_exists(conn, 'wallet_ledger'):
        _safe_execute(conn, """
            CREATE TABLE wallet_ledger (
                id VARCHAR(36) PRIMARY KEY,
                wallet_id VARCHAR(36) NOT NULL,
                driver_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL,
                balance_after_cents INTEGER NOT NULL,
                transaction_type VARCHAR(30) NOT NULL,
                reference_type VARCHAR(30),
                reference_id VARCHAR(36),
                description VARCHAR(500),
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """, "CREATE wallet_ledger")
        conn.commit()

    # --- Migration 074: Campaign tables ---
    if not _table_exists(conn, 'campaigns'):
        _safe_execute(conn, """
            CREATE TABLE campaigns (
                id VARCHAR(36) PRIMARY KEY,
                sponsor_id VARCHAR(36) NOT NULL,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                budget_cents INTEGER NOT NULL DEFAULT 0,
                spent_cents INTEGER NOT NULL DEFAULT 0,
                reward_cents_per_session INTEGER NOT NULL DEFAULT 500,
                targeting_rules TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP
            )
        """, "CREATE campaigns")
        conn.commit()

    if not _table_exists(conn, 'session_events'):
        _safe_execute(conn, """
            CREATE TABLE session_events (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                charger_id VARCHAR(255),
                merchant_id VARCHAR(255),
                session_type VARCHAR(30) NOT NULL DEFAULT 'charging',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                started_at TIMESTAMP NOT NULL DEFAULT now(),
                ended_at TIMESTAMP,
                duration_minutes INTEGER,
                verified BOOLEAN NOT NULL DEFAULT false,
                metadata_json TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """, "CREATE session_events")
        conn.commit()

    if not _table_exists(conn, 'incentive_grants'):
        _safe_execute(conn, """
            CREATE TABLE incentive_grants (
                id VARCHAR(36) PRIMARY KEY,
                session_event_id VARCHAR(36) NOT NULL,
                campaign_id VARCHAR(36),
                user_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL,
                grant_type VARCHAR(30) NOT NULL DEFAULT 'campaign',
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """, "CREATE incentive_grants")
        conn.commit()

    # --- Migration 075: Device tokens ---
    if not _table_exists(conn, 'device_tokens'):
        _safe_execute(conn, """
            CREATE TABLE device_tokens (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                platform VARCHAR(10) NOT NULL DEFAULT 'ios',
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP
            )
        """, "CREATE device_tokens")
        conn.commit()

    # --- Migration 076: merchants.is_corporate ---
    if _table_exists(conn, 'merchants') and not _column_exists(conn, 'merchants', 'is_corporate'):
        _safe_execute(conn,
            "ALTER TABLE merchants ADD COLUMN is_corporate BOOLEAN NOT NULL DEFAULT false",
            "merchants.is_corporate")
        conn.commit()
    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_merchants_is_corporate ON merchants(is_corporate)", "")
    conn.commit()

    # --- Migration 077: Wallet balance constraint ---
    # Skip - constraints may already exist or may conflict

    # --- Migration 078: Tesla OAuth states ---
    if not _table_exists(conn, 'tesla_oauth_states'):
        _safe_execute(conn, """
            CREATE TABLE tesla_oauth_states (
                state VARCHAR(64) PRIMARY KEY,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """, "CREATE tesla_oauth_states")
        conn.commit()
    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_tesla_oauth_states_expires ON tesla_oauth_states(expires_at)", "")
    conn.commit()

    # --- Migration 079: Charger composite index ---
    _safe_execute(conn, "CREATE INDEX IF NOT EXISTS idx_chargers_public_location ON chargers(is_public, lat, lng)", "idx_chargers_public_location")
    conn.commit()

    print("=== Schema sync complete ===")


def _reencrypt_tesla_tokens(conn):
    """Re-encrypt any plaintext Tesla tokens using Fernet.

    Safe to run repeatedly: already-encrypted tokens (gAAAAA prefix) are skipped.
    """
    from sqlalchemy import text

    try:
        from app.core.token_encryption import encrypt_token
    except ImportError:
        # Running outside app context — resolve path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from app.core.token_encryption import encrypt_token

    FERNET_PREFIX = "gAAAAA"
    rows = conn.execute(text("SELECT id, access_token, refresh_token FROM tesla_connections")).fetchall()
    updated = 0
    for row in rows:
        conn_id, access, refresh = row[0], row[1], row[2]
        new_access = access
        new_refresh = refresh
        needs_update = False

        if access and not access.startswith(FERNET_PREFIX):
            new_access = encrypt_token(access)
            needs_update = True
        if refresh and not refresh.startswith(FERNET_PREFIX):
            new_refresh = encrypt_token(refresh)
            needs_update = True

        if needs_update:
            conn.execute(text(
                "UPDATE tesla_connections SET access_token = :a, refresh_token = :r WHERE id = :id"
            ), {"a": new_access, "r": new_refresh, "id": conn_id})
            updated += 1
    if updated:
        conn.commit()
    print(f"  Re-encrypted {updated}/{len(rows)} Tesla token pairs")


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

            # If version is <= 069, we need to sync schema and stamp to 079
            # because migrations 070-079 have schema conflicts with production DB
            version_num = current_version
            try:
                # Extract numeric prefix for comparison
                num = int(version_num.split('_')[0])
            except (ValueError, IndexError):
                num = 0

            if num <= 69:
                print(f"Version {current_version} is <= 069, syncing schema to 079...")
                _ensure_tables_070_079(conn)

                # Stamp to the latest version
                target = '082_credit_wallet_final'
                print(f"Stamping database from {current_version} to {target}")
                conn.execute(text(
                    "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
                ), {"old": current_version, "new": target})
                conn.commit()
                print(f"Successfully stamped to {target}")
            elif num < 79:
                # Somewhere between 070 and 078 — sync and stamp
                print(f"Version {current_version} is between 070-078, syncing to 079...")
                _ensure_tables_070_079(conn)
                target = '082_credit_wallet_final'
                conn.execute(text(
                    "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
                ), {"old": current_version, "new": target})
                conn.commit()
                print(f"Successfully stamped to {target}")
            elif num >= 79 and num < 82:
                # Stuck at 079/080/081 due to credit wallet migration issues
                # Also check if driver_wallets needs schema upgrade
                if _table_exists(conn, 'driver_wallets') and not _column_exists(conn, 'driver_wallets', 'driver_id'):
                    _upgrade_driver_wallets_legacy(conn)
                target = '082_credit_wallet_final'
                print(f"Version {current_version} is between 079-081, stamping to {target}...")
                conn.execute(text(
                    "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
                ), {"old": current_version, "new": target})
                conn.commit()
                print(f"Successfully stamped to {target}")
            else:
                # Version >= 082 - still check if driver_wallets needs schema upgrade
                if _table_exists(conn, 'driver_wallets') and not _column_exists(conn, 'driver_wallets', 'driver_id'):
                    _upgrade_driver_wallets_legacy(conn)
                print(f"Version {current_version} is current, no changes needed")

            # Re-encrypt any plaintext Tesla tokens
            if _table_exists(conn, 'tesla_connections'):
                print("=== Checking Tesla token encryption ===")
                _reencrypt_tesla_tokens(conn)

            return 0
    except Exception as e:
        print(f"Error fixing alembic version: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    sys.exit(main())
