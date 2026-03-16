"""
End-to-end test: Session → Incentive Grant → Wallet Credit

Tests the full charging session lifecycle including:
1. Campaign creation and activation
2. Session creation and ending
3. IncentiveEngine evaluation and grant creation
4. Nova transaction creation
5. Wallet balance update and ledger entry
6. Campaign budget decrement (spent_cents, sessions_granted)

This test catches schema drift between ORM models and the actual database
by exercising every INSERT/UPDATE in the grant chain. If a column name
mismatch exists (e.g., ORM says "driver_user_id" but DB has "user_id"),
the INSERT will fail here just as it would in production.

Also validates raw SQL queries used in atomic operations match the
actual column names in the database.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text, inspect


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def driver(db):
    """Create a driver user."""
    from app.models.user import User
    user = User(
        email="e2e_driver@test.com",
        password_hash="hashed",
        is_active=True,
        role_flags="driver",
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def campaign(db, driver):
    """Create an active, funded campaign ready to grant."""
    from app.models.campaign import Campaign
    c = Campaign(
        id=str(uuid.uuid4()),
        sponsor_name="E2E Test Sponsor",
        name="E2E-Test-Campaign",
        campaign_type="custom",
        status="active",
        priority=50,
        budget_cents=10000,  # $100
        spent_cents=0,
        cost_per_session_cents=40,  # $0.40
        sessions_granted=0,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        rule_min_duration_minutes=1,
        created_by_user_id=driver.id,
        created_at=datetime.utcnow(),
    )
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def ended_session(db, driver, campaign):
    """Create a completed charging session (already ended)."""
    from app.models.session_event import SessionEvent
    now = datetime.utcnow()
    s = SessionEvent(
        id=str(uuid.uuid4()),
        driver_user_id=driver.id,
        charger_id=None,
        charger_network="Tesla",
        session_start=now - timedelta(minutes=30),
        session_end=now,
        duration_minutes=30,
        kwh_delivered=8.5,
        battery_start_pct=60,
        battery_end_pct=80,
        quality_score=90,
        source="tesla_api",
        verified=True,
        ended_reason="unplugged",
        created_at=now - timedelta(minutes=30),
        updated_at=now,
    )
    db.add(s)
    db.flush()
    return s


# ── Core E2E Test ─────────────────────────────────────────────────────

class TestSessionToWalletE2E:
    """Full flow: session end → incentive evaluation → grant → wallet credit."""

    def test_full_grant_flow(self, db, driver, campaign, ended_session):
        """
        The critical path: evaluate a session, create a grant, credit the wallet.

        This test exercises every table INSERT/UPDATE in the grant chain.
        If any column name doesn't match between ORM and DB, this fails.
        """
        from app.services.incentive_engine import IncentiveEngine
        from app.models.session_event import IncentiveGrant
        from app.models.driver_wallet import DriverWallet, WalletLedger

        # ── Step 1: Evaluate session against campaign ──
        grant = IncentiveEngine.evaluate_session(db, ended_session)

        assert grant is not None, (
            f"Grant should be created. Session: duration={ended_session.duration_minutes}min, "
            f"campaign min_duration={campaign.rule_min_duration_minutes}min"
        )
        assert grant.amount_cents == campaign.cost_per_session_cents
        assert grant.status == "granted"

        # ── Step 2: Verify grant is queryable ──
        fetched_grant = db.query(IncentiveGrant).filter(
            IncentiveGrant.session_event_id == ended_session.id
        ).first()
        assert fetched_grant is not None, "Grant should be queryable by session_event_id"
        assert fetched_grant.driver_user_id == driver.id

        # ── Step 3: Verify campaign budget was decremented ──
        db.expire(campaign)  # Force re-read from DB
        assert campaign.spent_cents == 40, (
            f"Campaign spent_cents should be 40 but got {campaign.spent_cents}"
        )
        assert campaign.sessions_granted == 1, (
            f"Campaign sessions_granted should be 1 but got {campaign.sessions_granted}"
        )

        # ── Step 4: Verify wallet was created and credited ──
        wallet = db.query(DriverWallet).filter(
            DriverWallet.driver_id == driver.id
        ).first()
        assert wallet is not None, "Wallet should be auto-created on first grant"
        assert wallet.balance_cents == 40, (
            f"Wallet balance should be 40 cents but got {wallet.balance_cents}"
        )
        assert wallet.total_earned_cents == 40

        # ── Step 5: Verify wallet ledger entry ──
        ledger = db.query(WalletLedger).filter(
            WalletLedger.wallet_id == wallet.id
        ).first()
        assert ledger is not None, "Ledger entry should exist"
        assert ledger.amount_cents == 40
        assert ledger.transaction_type == "credit"
        assert ledger.reference_type == "campaign_grant"
        assert ledger.reference_id == grant.id

    def test_grant_idempotency(self, db, driver, campaign, ended_session):
        """Calling evaluate_session twice should not create duplicate grants."""
        from app.services.incentive_engine import IncentiveEngine

        grant1 = IncentiveEngine.evaluate_session(db, ended_session)
        assert grant1 is not None

        # Second call should return existing grant (idempotent)
        grant2 = IncentiveEngine.evaluate_session(db, ended_session)
        assert grant2 is not None
        assert grant2.id == grant1.id, "Should return same grant, not create duplicate"

        # Campaign budget should only be decremented once
        db.expire(campaign)
        assert campaign.spent_cents == 40, (
            f"Budget should be decremented once (40), got {campaign.spent_cents}"
        )
        assert campaign.sessions_granted == 1

    def test_no_grant_for_short_session(self, db, driver, campaign):
        """Sessions shorter than min_duration should NOT get a grant."""
        from app.models.session_event import SessionEvent
        from app.services.incentive_engine import IncentiveEngine

        # Set campaign min to 30 min
        campaign.rule_min_duration_minutes = 30
        db.flush()

        now = datetime.utcnow()
        short_session = SessionEvent(
            id=str(uuid.uuid4()),
            driver_user_id=driver.id,
            session_start=now - timedelta(minutes=5),
            session_end=now,
            duration_minutes=5,
            quality_score=80,
            source="tesla_api",
            verified=True,
            ended_reason="unplugged",
            created_at=now,
            updated_at=now,
        )
        db.add(short_session)
        db.flush()

        grant = IncentiveEngine.evaluate_session(db, short_session)
        assert grant is None, "Short session should not receive a grant"

        db.expire(campaign)
        assert campaign.spent_cents == 0, "Budget should not be decremented"
        assert campaign.sessions_granted == 0

    def test_budget_exhaustion_stops_grants(self, db, driver, campaign):
        """When budget runs out, no more grants should be created."""
        from app.models.session_event import SessionEvent
        from app.services.incentive_engine import IncentiveEngine

        # Set tiny budget — exactly enough for 1 grant
        campaign.budget_cents = 40
        campaign.cost_per_session_cents = 40
        db.flush()

        now = datetime.utcnow()

        # First session — should get grant
        s1 = SessionEvent(
            id=str(uuid.uuid4()),
            driver_user_id=driver.id,
            session_start=now - timedelta(minutes=10),
            session_end=now - timedelta(minutes=1),
            duration_minutes=9,
            quality_score=80,
            source="tesla_api",
            verified=True,
            ended_reason="unplugged",
            created_at=now,
            updated_at=now,
        )
        db.add(s1)
        db.flush()

        grant1 = IncentiveEngine.evaluate_session(db, s1)
        assert grant1 is not None, "First session should get a grant"

        # Second session — budget exhausted
        s2 = SessionEvent(
            id=str(uuid.uuid4()),
            driver_user_id=driver.id,
            session_start=now - timedelta(minutes=5),
            session_end=now,
            duration_minutes=5,
            quality_score=80,
            source="tesla_api",
            verified=True,
            ended_reason="unplugged",
            created_at=now,
            updated_at=now,
        )
        db.add(s2)
        db.flush()

        grant2 = IncentiveEngine.evaluate_session(db, s2)
        assert grant2 is None, "Second session should NOT get a grant (budget exhausted)"


# ── Schema Drift Detection ────────────────────────────────────────────

class TestSchemaDriftDetection:
    """
    Verify that ORM model column definitions match what the database actually has.

    These tests catch the class of bugs where an ORM Column("actual_name", ...)
    mapping diverges from what migrations created. While SQLite tests always match
    (since create_all() uses ORM), this at least ensures the ORM is internally
    consistent and that raw SQL queries reference correct column names.
    """

    def test_incentive_grant_columns_exist(self, db):
        """Verify all IncentiveGrant ORM columns exist in the database."""
        from app.models.session_event import IncentiveGrant
        inspector = inspect(db.bind)
        db_columns = {c["name"] for c in inspector.get_columns("incentive_grants")}

        # These are the columns the grant flow writes to
        required = {
            "id", "session_event_id", "campaign_id", "user_id",
            "amount_cents", "status", "reward_destination",
            "idempotency_key", "granted_at", "created_at",
        }
        missing = required - db_columns
        assert not missing, (
            f"incentive_grants missing columns: {missing}. "
            f"DB has: {sorted(db_columns)}"
        )

    def test_session_event_columns_exist(self, db):
        """Verify key SessionEvent columns exist in the database."""
        inspector = inspect(db.bind)
        db_columns = {c["name"] for c in inspector.get_columns("session_events")}

        required = {
            "id", "driver_user_id", "session_start", "session_end",
            "duration_minutes", "charger_id", "charger_network",
            "quality_score", "ended_reason", "next_poll_at",
        }
        missing = required - db_columns
        assert not missing, (
            f"session_events missing columns: {missing}. "
            f"DB has: {sorted(db_columns)}"
        )

    def test_driver_wallet_columns_exist(self, db):
        """Verify DriverWallet columns used by grant flow exist."""
        inspector = inspect(db.bind)
        db_columns = {c["name"] for c in inspector.get_columns("driver_wallets")}

        required = {
            "id", "driver_id", "balance_cents", "total_earned_cents",
            "pending_balance_cents",
        }
        missing = required - db_columns
        assert not missing, (
            f"driver_wallets missing columns: {missing}. "
            f"DB has: {sorted(db_columns)}"
        )

    def test_campaign_budget_columns_for_raw_sql(self, db):
        """
        Verify the columns referenced in decrement_budget_atomic() raw SQL exist.

        The atomic UPDATE uses: spent_cents, sessions_granted, budget_cents, status, id
        If any of these column names change, the raw SQL silently fails.
        """
        inspector = inspect(db.bind)
        db_columns = {c["name"] for c in inspector.get_columns("campaigns")}

        # These are referenced in the raw SQL UPDATE
        raw_sql_columns = {
            "id", "spent_cents", "sessions_granted",
            "budget_cents", "status", "updated_at",
        }
        missing = raw_sql_columns - db_columns
        assert not missing, (
            f"campaigns table missing columns used by raw SQL: {missing}. "
            f"decrement_budget_atomic() will silently fail! "
            f"DB has: {sorted(db_columns)}"
        )

    def test_raw_sql_budget_decrement_works(self, db, driver, campaign):
        """
        Directly test the raw SQL used by decrement_budget_atomic().

        This catches mismatches between raw SQL column names and DB schema
        that ORM queries would hide.
        """
        from app.services.campaign_service import CampaignService

        initial_spent = campaign.spent_cents
        initial_sessions = campaign.sessions_granted

        result = CampaignService.decrement_budget_atomic(db, campaign.id, 40)
        assert result is True, "Budget decrement should succeed"

        # Force re-read from DB (bypass ORM cache)
        db.expire(campaign)
        assert campaign.spent_cents == initial_spent + 40, (
            f"spent_cents should be {initial_spent + 40}, got {campaign.spent_cents}"
        )
        assert campaign.sessions_granted == initial_sessions + 1, (
            f"sessions_granted should be {initial_sessions + 1}, got {campaign.sessions_granted}"
        )

    def test_nova_transaction_insert_works(self, db, driver):
        """
        Test that NovaTransaction can be created without FK violations.

        This catches the session_id FK issue (points to domain_charging_sessions)
        and the campaign_id column that doesn't exist in prod.
        """
        from app.models.domain import NovaTransaction

        tx = NovaTransaction(
            id=str(uuid.uuid4()),
            type="campaign_grant",
            driver_user_id=driver.id,
            amount=40,
            session_id=None,  # Must be None — FK points to legacy table
            metadata={"source": "e2e_test"},
            idempotency_key=f"e2e_test_{uuid.uuid4()}",
            payload_hash="test_hash",
            created_at=datetime.utcnow(),
        )
        db.add(tx)
        db.flush()

        # Verify it's queryable
        fetched = db.query(NovaTransaction).filter(
            NovaTransaction.id == tx.id
        ).first()
        assert fetched is not None
        assert fetched.amount == 40
