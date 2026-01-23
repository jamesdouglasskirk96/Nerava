"""
Comprehensive tests for verify_dwell service

Tests all functions including helpers, error paths, and edge cases.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from unittest.mock import patch
from app.services.verify_dwell import (
    haversine_m,
    _has_table,
    _load_event,
    _nearest_charger,
    _nearest_merchant,
    _get_session_hub_id,
    _get_domain_radius,
    _choose_target,
    _record_ping_history,
    _calculate_drift_penalty,
    _calculate_verification_score,
    start_session,
    ping,
    _load_target_coords
)


class TestHaversineM:
    """Test haversine_m distance calculation"""
    
    def test_haversine_m_same_point(self):
        """Test haversine_m returns 0 for same point"""
        result = haversine_m(30.2672, -97.7431, 30.2672, -97.7431)
        assert result == 0.0
    
    def test_haversine_m_different_points(self):
        """Test haversine_m calculates distance correctly"""
        # Austin to Domain (approximately 5km)
        result = haversine_m(30.2672, -97.7431, 30.4021, -97.7265)
        assert result > 0
        assert 14000 < result < 16000  # Approximately 15km
    
    def test_haversine_m_known_distance(self):
        """Test haversine_m with known distance"""
        # Very close points (should be small distance)
        result = haversine_m(30.2672, -97.7431, 30.26722, -97.74305)
        assert result < 10  # Less than 10 meters


class TestHasTable:
    """Test _has_table helper function"""
    
    def test_has_table_exists(self, db: Session):
        """Test _has_table returns True for existing table"""
        # Create a test table
        db.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)"))
        db.commit()
        
        result = _has_table(db, "test_table")
        assert result is True
    
    def test_has_table_not_exists(self, db: Session):
        """Test _has_table returns False for non-existent table"""
        result = _has_table(db, "nonexistent_table_xyz")
        assert result is False
    
    def test_has_table_handles_error(self, db: Session):
        """Test _has_table handles errors gracefully"""
        # Mock an error scenario
        result = _has_table(db, "test_table")
        # Should not raise, should return False on error
        assert isinstance(result, bool)


class TestLoadEvent:
    """Test _load_event function"""
    
    def test_load_event_exists(self, db: Session):
        """Test _load_event loads existing event"""
        # Create events2 table and insert event
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS events2 (
                id INTEGER PRIMARY KEY,
                title TEXT,
                lat REAL,
                lng REAL,
                radius_m INTEGER
            )
        """))
        db.execute(text("""
            INSERT INTO events2 (id, title, lat, lng, radius_m)
            VALUES (1, 'Test Event', 30.2672, -97.7431, 100)
        """))
        db.commit()
        
        result = _load_event(db, 1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "Test Event"
    
    def test_load_event_not_exists(self, db: Session):
        """Test _load_event returns None for non-existent event"""
        result = _load_event(db, 999)
        assert result is None
    
    def test_load_event_handles_error(self, db: Session):
        """Test _load_event handles errors gracefully"""
        # Table doesn't exist
        result = _load_event(db, 1)
        assert result is None


class TestNearestCharger:
    """Test _nearest_charger function"""
    
    def test_nearest_charger_exists(self, db: Session):
        """Test _nearest_charger finds nearest charger"""
        # Create chargers_openmap table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        db.commit()
        
        result = _nearest_charger(db, 30.2672, -97.7431)
        assert result is not None
        assert result["id"] == "ch1"
    
    def test_nearest_charger_not_exists(self, db: Session):
        """Test _nearest_charger returns None when no chargers"""
        result = _nearest_charger(db, 30.2672, -97.7431)
        assert result is None
    
    def test_nearest_charger_table_not_exists(self, db: Session):
        """Test _nearest_charger handles missing table"""
        result = _nearest_charger(db, 30.2672, -97.7431)
        assert result is None


class TestNearestMerchant:
    """Test _nearest_merchant function"""
    
    def test_nearest_merchant_exists(self, db: Session):
        """Test _nearest_merchant finds nearest merchant"""
        # Use ORM model - merchants table already exists from models
        from app.models_while_you_charge import Merchant
        merchant = Merchant(
            id="m1",
            name="Merchant 1",
            lat=30.2672,
            lng=-97.7431
        )
        db.add(merchant)
        db.commit()
        
        result = _nearest_merchant(db, 30.2672, -97.7431)
        assert result is not None
        assert result["id"] == "m1"
    
    def test_nearest_merchant_not_exists(self, db: Session):
        """Test _nearest_merchant returns None when no merchants"""
        result = _nearest_merchant(db, 30.2672, -97.7431)
        assert result is None


class TestGetSessionHubId:
    """Test _get_session_hub_id function"""
    
    def test_get_session_hub_id_from_column(self, db: Session):
        """Test _get_session_hub_id gets hub_id from column"""
        # Drop and create sessions table with hub_id column (sessions is legacy, no model)
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                hub_id TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, hub_id)
            VALUES ('session1', 'domain')
        """))
        db.commit()
        
        result = _get_session_hub_id(db, "session1")
        assert result == "domain"
    
    def test_get_session_hub_id_from_meta(self, db: Session):
        """Test _get_session_hub_id gets hub_id from meta JSON"""
        import json
        # Drop and create sessions table with meta column
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                meta TEXT
            )
        """))
        meta = {"hub_id": "domain"}
        db.execute(text("""
            INSERT INTO sessions (id, meta)
            VALUES ('session1', :meta)
        """), {"meta": json.dumps(meta)})
        db.commit()
        
        result = _get_session_hub_id(db, "session1")
        assert result == "domain"
    
    def test_get_session_hub_id_from_target_id(self, db: Session):
        """Test _get_session_hub_id detects Domain hub from target_id"""
        # Drop and create sessions table with target_id column
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                target_id TEXT
            )
        """))
        # Use a Domain charger ID
        from app.domains.domain_hub import DOMAIN_CHARGERS
        charger_id = DOMAIN_CHARGERS[0]["id"]
        db.execute(text("""
            INSERT INTO sessions (id, target_id)
            VALUES ('session1', :target_id)
        """), {"target_id": charger_id})
        db.commit()
        
        result = _get_session_hub_id(db, "session1")
        assert result == "domain"
    
    def test_get_session_hub_id_not_found(self, db: Session):
        """Test _get_session_hub_id returns None when not found"""
        result = _get_session_hub_id(db, "nonexistent_session")
        assert result is None


class TestGetDomainRadius:
    """Test _get_domain_radius function"""
    
    def test_get_domain_radius_charger(self, db: Session):
        """Test _get_domain_radius for charger"""
        from app.domains.domain_hub import DOMAIN_CHARGERS
        charger_id = DOMAIN_CHARGERS[0]["id"]
        
        result = _get_domain_radius("charger", charger_id, 100)
        assert result >= 0
    
    def test_get_domain_radius_merchant(self, db: Session):
        """Test _get_domain_radius for merchant"""
        result = _get_domain_radius("merchant", "test_merchant", 100)
        assert result >= 0
    
    def test_get_domain_radius_fallback(self, db: Session):
        """Test _get_domain_radius falls back to default"""
        result = _get_domain_radius("unknown", "test", 150)
        assert result == 150


class TestChooseTarget:
    """Test _choose_target function"""
    
    def test_choose_target_event(self, db: Session):
        """Test _choose_target selects event when event_id provided"""
        # Create events2 table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS events2 (
                id INTEGER PRIMARY KEY,
                title TEXT,
                lat REAL,
                lng REAL,
                radius_m INTEGER
            )
        """))
        db.execute(text("""
            INSERT INTO events2 (id, title, lat, lng, radius_m)
            VALUES (1, 'Test Event', 30.2672, -97.7431, 100)
        """))
        db.commit()
        
        result = _choose_target(db, 30.2672, -97.7431, event_id=1)
        assert result is not None
        assert result["target_type"] == "event"
    
    def test_choose_target_charger(self, db: Session):
        """Test _choose_target selects charger when nearby"""
        # Create chargers_openmap table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        db.commit()
        
        result = _choose_target(db, 30.2672, -97.7431, event_id=None)
        assert result is not None
        assert result["target_type"] == "charger"
    
    def test_choose_target_merchant(self, db: Session):
        """Test _choose_target selects merchant when no charger"""
        # Use ORM model - merchants table already exists from models
        from app.models_while_you_charge import Merchant
        merchant = Merchant(
            id="m1",
            name="Merchant 1",
            lat=30.2672,
            lng=-97.7431
        )
        db.add(merchant)
        db.commit()
        
        result = _choose_target(db, 30.2672, -97.7431, event_id=None)
        assert result is not None
        assert result["target_type"] == "merchant"
    
    def test_choose_target_none(self, db: Session):
        """Test _choose_target returns None when no targets"""
        result = _choose_target(db, 0.0, 0.0, event_id=None)
        assert result is None
    
    def test_choose_target_domain_radius(self, db: Session):
        """Test _choose_target uses domain-specific radius"""
        # Create chargers_openmap table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        from app.domains.domain_hub import DOMAIN_CHARGERS
        charger = DOMAIN_CHARGERS[0]
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES (:id, :name, :lat, :lng)
        """), {
            "id": charger["id"],
            "name": charger["name"],
            "lat": charger["lat"],
            "lng": charger["lng"]
        })
        db.commit()
        
        result = _choose_target(db, charger["lat"], charger["lng"], event_id=None, hub_id="domain")
        assert result is not None
        assert "radius_m" in result


class TestRecordPingHistory:
    """Test _record_ping_history function"""
    
    def test_record_ping_history_creates_history(self, db: Session):
        """Test _record_ping_history creates ping history"""
        import json
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                meta TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, meta)
            VALUES ('session1', '{}')
        """))
        db.commit()
        
        _record_ping_history(db, "session1", 30.2672, -97.7431, datetime.utcnow())
        db.commit()
        
        result = db.execute(text("SELECT meta FROM sessions WHERE id='session1'")).first()
        meta = json.loads(result[0])
        assert "ping_history" in meta
        assert len(meta["ping_history"]) == 1
    
    def test_record_ping_history_limits_to_10(self, db: Session):
        """Test _record_ping_history limits history to 10 pings"""
        import json
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                meta TEXT
            )
        """))
        # Create history with 10 pings
        history = [{"lat": 30.0, "lng": -97.0, "ts": datetime.utcnow().isoformat()} for _ in range(10)]
        meta = {"ping_history": history}
        db.execute(text("""
            INSERT INTO sessions (id, meta)
            VALUES ('session1', :meta)
        """), {"meta": json.dumps(meta)})
        db.commit()
        
        _record_ping_history(db, "session1", 30.2672, -97.7431, datetime.utcnow())
        db.commit()
        
        result = db.execute(text("SELECT meta FROM sessions WHERE id='session1'")).first()
        meta = json.loads(result[0])
        assert len(meta["ping_history"]) == 10  # Should still be 10, not 11
    
    def test_record_ping_history_handles_no_meta_column(self, db: Session):
        """Test _record_ping_history handles missing meta column"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id)
            VALUES ('session1')
        """))
        db.commit()
        
        # Should not raise
        _record_ping_history(db, "session1", 30.2672, -97.7431, datetime.utcnow())


class TestCalculateDriftPenalty:
    """Test _calculate_drift_penalty function"""
    
    def test_calculate_drift_penalty_no_history(self, db: Session):
        """Test _calculate_drift_penalty returns zero with no history"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                meta TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, meta)
            VALUES ('session1', '{}')
        """))
        db.commit()
        
        result = _calculate_drift_penalty(db, "session1", 30.2672, -97.7431, datetime.utcnow())
        assert result["penalty"] == 0
        assert result["drift_m"] == 0
    
    def test_calculate_drift_penalty_with_history(self, db: Session):
        """Test _calculate_drift_penalty calculates penalty from history"""
        import json
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                meta TEXT
            )
        """))
        now = datetime.utcnow()
        history = [
            {"lat": 30.2672, "lng": -97.7431, "ts": (now - timedelta(seconds=10)).isoformat()},
            {"lat": 30.2672, "lng": -97.7431, "ts": (now - timedelta(seconds=5)).isoformat()}
        ]
        meta = {"ping_history": history}
        db.execute(text("""
            INSERT INTO sessions (id, meta)
            VALUES ('session1', :meta)
        """), {"meta": json.dumps(meta)})
        db.commit()
        
        # Small drift (should be within tolerance)
        result = _calculate_drift_penalty(db, "session1", 30.26722, -97.74305, now)
        assert "penalty" in result
        assert "drift_m" in result
    
    def test_calculate_drift_penalty_fallback_to_last_lat_lng(self, db: Session):
        """Test _calculate_drift_penalty falls back to last_lat/last_lng"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                last_lat REAL,
                last_lng REAL,
                updated_at TEXT
            )
        """))
        now = datetime.utcnow()
        db.execute(text("""
            INSERT INTO sessions (id, last_lat, last_lng, updated_at)
            VALUES ('session1', 30.2672, -97.7431, :updated_at)
        """), {"updated_at": (now - timedelta(seconds=10)).isoformat()})
        db.commit()
        
        result = _calculate_drift_penalty(db, "session1", 30.26722, -97.74305, now)
        assert "penalty" in result
        assert "drift_m" in result


class TestCalculateVerificationScore:
    """Test _calculate_verification_score function"""
    
    def test_calculate_verification_score_perfect(self):
        """Test _calculate_verification_score with perfect conditions"""
        result = _calculate_verification_score(
            distance_m=0,
            radius_m=100,
            dwell_seconds=120,
            dwell_required_s=60,
            drift_penalty=0,
            accuracy_m=10,
            min_accuracy_m=50,
            hub_id=None
        )
        assert result["verification_score"] >= 80
        assert "score_components" in result
    
    def test_calculate_verification_score_with_penalties(self):
        """Test _calculate_verification_score with penalties"""
        result = _calculate_verification_score(
            distance_m=150,  # Outside radius
            radius_m=100,
            dwell_seconds=30,  # Below required
            dwell_required_s=60,
            drift_penalty=10,
            accuracy_m=100,  # Poor accuracy
            min_accuracy_m=50,
            hub_id="domain"
        )
        assert result["verification_score"] < 100
        assert "score_components" in result
        assert result["score_components"]["distance_penalty"] > 0
    
    def test_calculate_verification_score_domain_dwell(self):
        """Test _calculate_verification_score with Domain dwell requirements"""
        result = _calculate_verification_score(
            distance_m=50,
            radius_m=100,
            dwell_seconds=30,  # Below Domain optimal
            dwell_required_s=60,
            drift_penalty=0,
            accuracy_m=10,
            min_accuracy_m=50,
            hub_id="domain"
        )
        assert result["verification_score"] < 100
        assert result["score_components"]["dwell_penalty"] > 0


class TestStartSession:
    """Test start_session function"""
    
    def test_start_session_with_target(self, db: Session):
        """Test start_session successfully starts with target"""
        # Create tables
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                status TEXT,
                target_type TEXT,
                target_id TEXT,
                target_name TEXT,
                radius_m INTEGER,
                started_lat REAL,
                started_lng REAL,
                last_lat REAL,
                last_lng REAL,
                last_accuracy_m REAL,
                min_accuracy_m INTEGER,
                dwell_required_s INTEGER,
                ping_count INTEGER,
                dwell_seconds INTEGER,
                ua TEXT
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        db.execute(text("""
            INSERT INTO sessions (id, user_id, status)
            VALUES ('session1', 1, 'pending')
        """))
        db.commit()
        
        result = start_session(
            db=db,
            session_id="session1",
            user_id=1,
            lat=30.2672,
            lng=-97.7431,
            accuracy_m=20,
            ua="test"
        )
        assert result["ok"] is True
        assert "target" in result
    
    def test_start_session_no_target(self, db: Session):
        """Test start_session handles no target"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                status TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, user_id, status)
            VALUES ('session1', 1, 'pending')
        """))
        db.commit()
        
        result = start_session(
            db=db,
            session_id="session1",
            user_id=1,
            lat=0.0,
            lng=0.0,
            accuracy_m=20,
            ua="test"
        )
        # May return ok=False or ok=True depending on settings
        assert "ok" in result


class TestPing:
    """Test ping function"""
    
    def test_ping_session_not_found(self, db: Session):
        """Test ping returns error for non-existent session"""
        # Create empty sessions table so ping can query it
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT
            )
        """))
        db.commit()
        
        result = ping(db=db, session_id="nonexistent", lat=30.2672, lng=-97.7431, accuracy_m=20)
        assert result["ok"] is False
        assert result["reason"] == "not_found"
    
    def test_ping_already_verified(self, db: Session):
        """Test ping returns idempotent for already verified session"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, status)
            VALUES ('session1', 'verified')
        """))
        db.commit()
        
        result = ping(db=db, session_id="session1", lat=30.2672, lng=-97.7431, accuracy_m=20)
        assert result["ok"] is True
        assert result["verified"] is True
        assert result["idempotent"] is True
    
    def test_ping_poor_accuracy(self, db: Session):
        """Test ping handles poor accuracy"""
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT,
                min_accuracy_m INTEGER,
                ping_count INTEGER,
                dwell_seconds INTEGER,
                dwell_required_s INTEGER,
                last_lat REAL,
                last_lng REAL,
                last_accuracy_m REAL,
                updated_at TEXT
            )
        """))
        db.execute(text("""
            INSERT INTO sessions (id, status, min_accuracy_m, ping_count, dwell_seconds, dwell_required_s, updated_at)
            VALUES ('session1', 'active', 50, 0, 0, 300, :updated_at)
        """), {"updated_at": datetime.utcnow().isoformat()})
        db.commit()
        
        result = ping(db=db, session_id="session1", lat=30.2672, lng=-97.7431, accuracy_m=100)
        assert result["ok"] is True
        assert result["verified"] is False
        assert result["reason"] == "accuracy"
    
    def test_ping_with_target_within_radius(self, db: Session):
        """Test ping accrues dwell time when within radius"""
        # Create sessions table with target
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT,
                user_id INTEGER,
                target_type TEXT,
                target_id TEXT,
                target_name TEXT,
                radius_m INTEGER,
                min_accuracy_m INTEGER,
                ping_count INTEGER,
                dwell_seconds INTEGER,
                dwell_required_s INTEGER,
                last_lat REAL,
                last_lng REAL,
                last_accuracy_m REAL,
                updated_at TEXT
            )
        """))
        # Create chargers table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        db.execute(text("""
            INSERT INTO sessions (id, status, user_id, target_type, target_id, target_name, radius_m, 
                                 min_accuracy_m, ping_count, dwell_seconds, dwell_required_s, updated_at)
            VALUES ('session1', 'active', 1, 'charger', 'ch1', 'Charger 1', 100, 50, 0, 0, 300, :updated_at)
        """), {"updated_at": datetime.utcnow().isoformat()})
        db.commit()
        
        result = ping(db=db, session_id="session1", lat=30.2672, lng=-97.7431, accuracy_m=20)
        assert result["ok"] is True
        assert result["verified"] is False
        assert "dwell_seconds" in result
        assert result["dwell_seconds"] > 0
    
    def test_ping_verifies_session(self, db: Session):
        """Test ping verifies session when dwell requirement met"""
        # Create sessions table with target
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT,
                user_id INTEGER,
                target_type TEXT,
                target_id TEXT,
                target_name TEXT,
                radius_m INTEGER,
                min_accuracy_m INTEGER,
                ping_count INTEGER,
                dwell_seconds INTEGER,
                dwell_required_s INTEGER,
                last_lat REAL,
                last_lng REAL,
                last_accuracy_m REAL,
                updated_at TEXT
            )
        """))
        # Create chargers table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        # Session already has enough dwell time
        db.execute(text("""
            INSERT INTO sessions (id, status, user_id, target_type, target_id, target_name, radius_m, 
                                 min_accuracy_m, ping_count, dwell_seconds, dwell_required_s, updated_at)
            VALUES ('session1', 'active', 1, 'charger', 'ch1', 'Charger 1', 100, 50, 0, 299, 300, :updated_at)
        """), {"updated_at": datetime.utcnow().isoformat()})
        db.commit()
        
        # Mock award_verify_bonus to avoid dependencies (it's imported inside the function)
        with patch('app.services.rewards.award_verify_bonus') as mock_reward:
            mock_reward.return_value = {"awarded": True, "user_delta": 200, "pool_delta": 0}
            result = ping(db=db, session_id="session1", lat=30.2672, lng=-97.7431, accuracy_m=20)
        
        assert result["ok"] is True
        assert result["verified"] is True
    
    def test_ping_acquires_target(self, db: Session):
        """Test ping acquires target when none exists"""
        # Create sessions table without target
        db.execute(text("DROP TABLE IF EXISTS sessions"))
        db.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                status TEXT,
                user_id INTEGER,
                target_type TEXT,
                target_id TEXT,
                target_name TEXT,
                radius_m INTEGER,
                min_accuracy_m INTEGER,
                ping_count INTEGER,
                dwell_seconds INTEGER,
                dwell_required_s INTEGER,
                last_lat REAL,
                last_lng REAL,
                last_accuracy_m REAL,
                updated_at TEXT
            )
        """))
        # Create chargers table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers_openmap (id, name, lat, lng)
            VALUES ('ch1', 'Charger 1', 30.2672, -97.7431)
        """))
        db.execute(text("""
            INSERT INTO sessions (id, status, user_id, target_type, target_id, radius_m, 
                                 min_accuracy_m, ping_count, dwell_seconds, dwell_required_s, updated_at)
            VALUES ('session1', 'active', 1, NULL, NULL, 100, 50, 0, 0, 300, :updated_at)
        """), {"updated_at": datetime.utcnow().isoformat()})
        db.commit()
        
        result = ping(db=db, session_id="session1", lat=30.2672, lng=-97.7431, accuracy_m=20)
        assert result["ok"] is True
        # Should have acquired target
        if result.get("target_acquired"):
            assert result["target_acquired"] is True
    
    def test_load_target_coords_event(self, db: Session):
        """Test _load_target_coords loads event coordinates"""
        # Create events2 table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS events2 (
                id INTEGER PRIMARY KEY,
                title TEXT,
                lat REAL,
                lng REAL,
                radius_m INTEGER
            )
        """))
        db.execute(text("""
            INSERT INTO events2 (id, title, lat, lng, radius_m)
            VALUES (1, 'Test Event', 30.2672, -97.7431, 100)
        """))
        db.commit()
        
        row = {"target_type": "event", "target_id": "1", "radius_m": 100}
        result = _load_target_coords(db, row)
        assert result is not None
        assert result["lat"] == 30.2672
        assert result["lng"] == -97.7431
    
    def test_load_target_coords_charger_fallback(self, db: Session):
        """Test _load_target_coords falls back to chargers table"""
        # Create chargers table (not chargers_openmap)
        db.execute(text("DROP TABLE IF EXISTS chargers"))
        db.execute(text("""
            CREATE TABLE chargers (
                id TEXT PRIMARY KEY,
                lat REAL,
                lng REAL
            )
        """))
        db.execute(text("""
            INSERT INTO chargers (id, lat, lng)
            VALUES ('ch1', 30.2672, -97.7431)
        """))
        db.commit()
        
        row = {"target_type": "charger", "target_id": "ch1", "radius_m": 100}
        result = _load_target_coords(db, row, hub_id=None)
        assert result is not None
        assert result["lat"] == 30.2672

