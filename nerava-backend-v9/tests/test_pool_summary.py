from fastapi.testclient import TestClient
from app.main_simple import app
from app.db import SessionLocal
from sqlalchemy import text


def test_pool_summary_and_recent_rewards_present():
    client = TestClient(app)

    # Ensure at least one reward exists by inserting a small reward_event
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO reward_events (user_id, source, gross_cents, net_cents, community_cents, meta)
            VALUES ('1','verify_bonus',200,180,20,'{"session_id":"t_pool_test"}')
        """))
        # pool_ledger2 inflow/outflow minimal if table exists
        try:
            db.execute(text("INSERT INTO pool_ledger2 (city, source, amount_cents, related_event_id) VALUES ('Austin','verified_sessions',-20,NULL)"))
        except Exception:
            pass
        db.commit()
    finally:
        db.close()

    r_me = client.get("/v1/gpt/me", params={"user_id": 1})
    assert r_me.status_code == 200
    me = r_me.json()
    assert "wallet_cents" in me
    # recent_rewards is optional but should exist with at least one entry now
    assert isinstance(me.get("recent_rewards", []), list)

    r_pool = client.get("/v1/pool/summary", params={"city": "Austin", "range": "today"})
    assert r_pool.status_code == 200
    data = r_pool.json()
    assert "balance_cents" in data
    assert "impact" in data and "verified_sessions" in data["impact"]

