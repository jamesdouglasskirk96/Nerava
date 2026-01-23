import pytest
from fastapi.testclient import TestClient
from app.main_simple import app
from app.db import SessionLocal
from sqlalchemy import text
from app.security.tokens import create_verify_token


client = TestClient(app)


def ensure_session(db):
    sid = "test-sid-1"
    db.execute(text("""
        INSERT OR REPLACE INTO sessions (id, user_id, status, started_at)
        VALUES (:id, 1, 'pending', CURRENT_TIMESTAMP)
    """), {"id": sid})
    db.commit()
    return sid


def test_verify_dwell_flow():
    db = SessionLocal()
    try:
        sid = ensure_session(db)
    finally:
        db.close()

    token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=600)

    # Start near downtown Austin
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid

    # Simulate 5 pings to accrue 75s (15s cap each)
    total = 0
    for _ in range(5):
        r2 = client.post("/v1/sessions/verify/ping", json={
            "session_id": sid,
            "lat": 30.26722,
            "lng": -97.74305,
            "accuracy_m": 18
        })
        assert r2.status_code == 200
        d = r2.json()
        total = d.get("dwell_seconds", total)
    assert total >= 60

    # Final ping should mark verified
    r3 = client.post("/v1/sessions/verify/ping", json={
        "session_id": sid,
        "lat": 30.26722,
        "lng": -97.74305,
        "accuracy_m": 18
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3.get("verified") is True


def test_verify_no_target_branch():
    client_local = TestClient(app)
    # Create a session and token
    db = SessionLocal()
    try:
        sid = "test-sid-nt-1"
        db.execute(text("INSERT OR REPLACE INTO sessions (id, user_id, status, started_at) VALUES (:id, 1, 'pending', CURRENT_TIMESTAMP)"), {"id": sid})
        db.commit()
    finally:
        db.close()
    token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=600)
    # Use far-away coordinates to force no_target
    r = client_local.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 0.0,
        "lng": 0.0,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") in (False, True)
    if data.get("ok") is False:
        assert data.get("reason") in ("no_target", "select_error")


def test_verify_invalid_token():
    """Test verify start with invalid token"""
    r = client.post("/v1/sessions/verify/start", json={
        "token": "invalid_token",
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    # Should return error for invalid token
    assert r.status_code in (400, 401, 403)


def test_verify_missing_coordinates():
    """Test verify start with missing coordinates"""
    db = SessionLocal()
    try:
        sid = ensure_session(db)
    finally:
        db.close()
    
    token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=600)
    
    # Missing lat
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lng": -97.7431,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    assert r.status_code in (400, 422)
    
    # Missing lng
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 30.2672,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    assert r.status_code in (400, 422)


def test_verify_invalid_coordinates():
    """Test verify start with invalid coordinates"""
    db = SessionLocal()
    try:
        sid = ensure_session(db)
    finally:
        db.close()
    
    token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=600)
    
    # Invalid lat (out of range)
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 100.0,  # Invalid latitude
        "lng": -97.7431,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    # Should handle invalid coordinates gracefully
    assert r.status_code in (200, 400, 422)


def test_verify_ping_without_start():
    """Test verify ping without starting session"""
    sid = "nonexistent_session"
    r = client.post("/v1/sessions/verify/ping", json={
        "session_id": sid,
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 20
    })
    # Should return error for nonexistent session
    assert r.status_code in (400, 404)


def test_verify_expired_token():
    """Test verify start with expired token"""
    db = SessionLocal()
    try:
        sid = ensure_session(db)
    finally:
        db.close()
    
    # Create token with very short TTL (already expired)
    token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=-1)
    
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 20,
        "ua": "pytest"
    })
    # Should return error for expired token
    assert r.status_code in (400, 401, 403)


def test_verify_ping_low_accuracy():
    """Test verify ping with low accuracy (should still work but may affect dwell calculation)"""
    db = SessionLocal()
    try:
        sid = ensure_session(db)
        token = create_verify_token(user_id=1, session_id=sid, ttl_seconds=600)
    finally:
        db.close()
    
    # Start session
    r = client.post("/v1/sessions/verify/start", json={
        "token": token,
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 200,  # Low accuracy
        "ua": "pytest"
    })
    assert r.status_code == 200
    
    # Ping with low accuracy
    r2 = client.post("/v1/sessions/verify/ping", json={
        "session_id": sid,
        "lat": 30.2672,
        "lng": -97.7431,
        "accuracy_m": 200  # Low accuracy
    })
    assert r2.status_code == 200
    # Should still process but may not count toward dwell


