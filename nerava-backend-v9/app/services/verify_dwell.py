from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.utils.log import get_logger


def haversine_m(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    from math import radians, cos, sin, asin, sqrt
    R = 6371000.0
    dlat = radians(b_lat - a_lat)
    dlng = radians(b_lng - a_lng)
    lat1 = radians(a_lat)
    lat2 = radians(b_lat)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(h))


logger = get_logger(__name__)


def _has_table(db: Session, name: str) -> bool:
    try:
        res = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"), {"n": name}).first()
        if res:
            return True
    except Exception:
        pass
    # Fallback via inspector (may fail on sqlite URLs outside context)
    try:
        from sqlalchemy import inspect
        return name in inspect(db.bind).get_table_names()
    except Exception:
        return False

def _load_event(db: Session, event_id: int) -> Optional[Dict[str, Any]]:
    try:
        row = db.execute(text("SELECT id, title, lat, lng, radius_m FROM events2 WHERE id=:id"), {"id": event_id}).mappings().first()
        return dict(row) if row else None
    except Exception as e:
        logger.warning({"at": "verify", "step": "load_event", "err": str(e)})
        return None


def _nearest_charger(db: Session, lat: float, lng: float) -> Optional[Dict[str, Any]]:
    try:
        if not _has_table(db, "chargers_openmap"):
            return None
        r = db.execute(text(
            "SELECT id, name, lat, lng FROM chargers_openmap WHERE ABS(lat-:lat)<0.1 AND ABS(lng-:lng)<0.1 ORDER BY ((lat-:lat)*(lat-:lat) + (lng-:lng)*(lng-:lng)) ASC LIMIT 1"
        ), {"lat": lat, "lng": lng}).mappings().first()
        return dict(r) if r else None
    except Exception as e:
        logger.info({"at": "verify", "step": "nearest_charger", "err": str(e)})
        return None


def _nearest_merchant(db: Session, lat: float, lng: float) -> Optional[Dict[str, Any]]:
    try:
        if not _has_table(db, "merchants"):
            return None
        r = db.execute(text(
            "SELECT id, name, lat, lng FROM merchants WHERE ABS(lat-:lat)<0.1 AND ABS(lng-:lng)<0.1 ORDER BY ((lat-:lat)*(lat-:lat) + (lng-:lng)*(lng-:lng)) ASC LIMIT 1"
        ), {"lat": lat, "lng": lng}).mappings().first()
        return dict(r) if r else None
    except Exception as e:
        logger.info({"at": "verify", "step": "nearest_merchant", "err": str(e)})
        return None


def _choose_target(db: Session, lat: float, lng: float, event_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if event_id:
        ev = _load_event(db, event_id)
        if ev:
            ev["target_type"] = "event"
            ev["target_id"] = str(ev["id"])
            ev["target_name"] = ev.get("title") or "Event"
            ev["radius_m"] = int(ev.get("radius_m") or settings.verify_default_radius_m)
            return ev
    ch = _nearest_charger(db, lat, lng)
    if ch:
        ch["target_type"] = "charger"
        ch["target_id"] = str(ch["id"])
        ch["target_name"] = ch.get("name") or "Charger"
        ch["radius_m"] = settings.verify_default_radius_m
        # verify distance within 150m
        if haversine_m(lat, lng, ch["lat"], ch["lng"]) <= 150:
            return ch
    m = _nearest_merchant(db, lat, lng)
    if m:
        m["target_type"] = "merchant"
        m["target_id"] = str(m["id"])
        m["target_name"] = m.get("name") or "Merchant"
        m["radius_m"] = settings.verify_default_radius_m
        if haversine_m(lat, lng, m["lat"], m["lng"]) <= 150:
            return m
    return None


def start_session(db: Session, *, session_id: str, user_id: int, lat: float, lng: float, accuracy_m: float, ua: str, event_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        has_events2 = _has_table(db, "events2")
        has_chargers = _has_table(db, "chargers_openmap")
        has_merchants = _has_table(db, "merchants")
        reason = None
        try:
            target = _choose_target(db, lat, lng, event_id)
        except Exception as e:
            logger.error({"at": "verify", "step": "start_choose", "uid": user_id, "sid": session_id, "err": str(e)})
            target = None
            reason = "select_error"

        min_acc = settings.verify_min_accuracy_m
        dwell_req = settings.verify_dwell_required_s
        radius_m = int(target.get("radius_m") if target else settings.verify_default_radius_m)

        # Idempotent baseline init (even without target)
        try:
            db.execute(text("""
                UPDATE sessions SET
                    target_type = COALESCE(target_type, :tt),
                    target_id = COALESCE(target_id, :ti),
                    target_name = COALESCE(target_name, :tn),
                    radius_m = COALESCE(radius_m, :rm),
                    started_lat = COALESCE(started_lat, :slat),
                    started_lng = COALESCE(started_lng, :slng),
                    last_lat = :llat,
                    last_lng = :llng,
                    last_accuracy_m = :acc,
                    min_accuracy_m = COALESCE(min_accuracy_m, :minacc),
                    dwell_required_s = COALESCE(dwell_required_s, :dreq),
                    ping_count = COALESCE(ping_count, 0),
                    dwell_seconds = COALESCE(dwell_seconds, 0),
                    status = CASE WHEN status IN ('pending','started') THEN 'active' ELSE status END,
                    ua = COALESCE(ua, :ua)
                WHERE id = :sid
            """), {
                "tt": target["target_type"] if target else ("unknown" if settings.verify_allow_start_without_target else None),
                "ti": target["target_id"] if target else None,
                "tn": target["target_name"] if target else None,
                "rm": radius_m,
                "slat": lat,
                "slng": lng,
                "llat": lat,
                "llng": lng,
                "acc": accuracy_m,
                "minacc": min_acc,
                "dreq": dwell_req,
                "ua": ua,
                "sid": session_id,
            })
            db.commit()
        except Exception as e:
            logger.error({"at": "verify", "step": "start_update", "uid": user_id, "sid": session_id, "err": str(e)})

        payload_base = {
            "at": "verify", "step": "start", "uid": user_id, "sid": session_id,
            "has_events2": has_events2, "has_chargers": has_chargers, "has_merchants": has_merchants,
        }

        if not target:
            logger.info({**payload_base, "ok": True if settings.verify_allow_start_without_target else False, "reason": reason or "no_target"})
            if settings.verify_allow_start_without_target:
                return {
                    "ok": True,
                    "session_id": session_id,
                    "reason": "no_target",
                    "hint": "Stay put; target will be acquired on first ping.",
                    "status": "started",
                    "dwell_required_s": dwell_req,
                    "min_accuracy_m": min_acc,
                }
            return {
                "ok": False,
                "reason": reason or "no_target",
                "hint": "Try moving 150m closer or widen radius.",
                "status": "start_failed",
                "session_id": session_id,
                "dwell_required_s": dwell_req,
                "min_accuracy_m": min_acc,
            }

        logger.info({**payload_base, "ok": True, "target_type": target.get("target_type")})
        return {
            "ok": True,
            "session_id": session_id,
            "target": {
                "type": target["target_type"],
                "id": target["target_id"],
                "name": target["target_name"],
                "lat": target["lat"],
                "lng": target["lng"],
                "radius_m": radius_m,
            },
            "status": "started",
            "dwell_required_s": dwell_req,
            "min_accuracy_m": min_acc,
        }
    except Exception as e:
        logger.error({"at": "verify", "step": "start", "ok": False, "sid": session_id, "exc": repr(e)})
        return {"ok": False, "reason": "internal_error", "hint": "Use ping to continue; start will self-heal.", "status": "start_failed"}


def _load_target_coords(db: Session, row) -> Optional[Dict[str, Any]]:
    ttype = row["target_type"]
    tid = row["target_id"]
    if not ttype or not tid:
        return None
    if ttype == "event":
        ev = _load_event(db, int(tid))
        if not ev:
            return None
        return {"lat": ev["lat"], "lng": ev["lng"], "radius_m": int(row["radius_m"] or settings.verify_default_radius_m)}
    if ttype == "charger":
        r = db.execute(text("SELECT lat, lng FROM chargers_openmap WHERE id=:id"), {"id": tid}).first()
        if not r:
            return None
        return {"lat": float(r[0]), "lng": float(r[1]), "radius_m": int(row["radius_m"] or settings.verify_default_radius_m)}
    if ttype == "merchant":
        r = db.execute(text("SELECT lat, lng FROM merchants WHERE id=:id"), {"id": tid}).first()
        if not r:
            return None
        return {"lat": float(r[0]), "lng": float(r[1]), "radius_m": int(row["radius_m"] or settings.verify_default_radius_m)}
    return None


def ping(db: Session, *, session_id: str, lat: float, lng: float, accuracy_m: float, ts: Optional[datetime] = None) -> Dict[str, Any]:
    row = db.execute(text("SELECT * FROM sessions WHERE id=:sid"), {"sid": session_id}).mappings().first()
    if not row:
        return {"ok": False, "reason": "not_found"}
    if row["status"] == "verified":
        return {"ok": True, "verified": True, "idempotent": True}

    # Accuracy gate
    min_acc = int(row.get("min_accuracy_m") or settings.verify_min_accuracy_m)
    if accuracy_m > min_acc:
        # Update last seen but do not accrue
        db.execute(text("""
            UPDATE sessions SET last_lat=:llat, last_lng=:llng, last_accuracy_m=:acc, ping_count=COALESCE(ping_count,0)+1
            WHERE id=:sid
        """), {"llat": lat, "llng": lng, "acc": accuracy_m, "sid": session_id})
        db.commit()
        return {"ok": True, "verified": False, "reason": "accuracy", "accuracy_m": accuracy_m, "min_accuracy_m": min_acc, "ping_count": int((row.get("ping_count") or 0) + 1)}

    target = _load_target_coords(db, row)
    # Self-heal: if no target yet, try to select once
    if not target:
        try:
            sel = _choose_target(db, lat, lng, None)
        except Exception as e:
            sel = None
            logger.info({"at": "verify", "step": "ping_choose", "sid": session_id, "err": str(e)})
        if sel:
            try:
                db.execute(text("""
                    UPDATE sessions SET target_type=:tt, target_id=:ti, target_name=:tn, radius_m=COALESCE(radius_m,:rm)
                    WHERE id=:sid AND (target_type IS NULL OR target_id IS NULL)
                """), {"tt": sel["target_type"], "ti": sel["target_id"], "tn": sel["target_name"], "rm": int(sel.get("radius_m") or settings.verify_default_radius_m), "sid": session_id})
                db.commit()
                target = {"lat": sel["lat"], "lng": sel["lng"], "radius_m": int(sel.get("radius_m") or settings.verify_default_radius_m)}
                acquired = True
            except Exception as e:
                logger.info({"at": "verify", "step": "ping_update_target", "sid": session_id, "err": str(e)})
                acquired = False
        else:
            acquired = False
    if not target:
        # No target yet; do not accrue
        db.execute(text("""
            UPDATE sessions SET last_lat=:llat, last_lng=:llng, last_accuracy_m=:acc, ping_count=COALESCE(ping_count,0)+1
            WHERE id=:sid
        """), {"llat": lat, "llng": lng, "acc": accuracy_m, "sid": session_id})
        db.commit()
        return {"ok": True, "verified": False, "reason": "no_target", "ping_count": int((row.get("ping_count") or 0) + 1)}

    distance_m = haversine_m(lat, lng, float(target["lat"]), float(target["lng"]))
    accrue = 0
    if distance_m <= float(target["radius_m"]):
        # Use server-time step with cap
        now = ts or datetime.utcnow()
        last_ts = row.get("updated_at")  # may not exist; fallback to 5s step
        step = settings.verify_ping_max_step_s
        accrue = step
    new_dwell = int(row.get("dwell_seconds") or 0) + int(accrue)
    db.execute(text("""
        UPDATE sessions SET
            last_lat=:llat, last_lng=:llng, last_accuracy_m=:acc,
            ping_count=COALESCE(ping_count,0)+1,
            dwell_seconds=:dwell,
            status=CASE WHEN :dwell >= COALESCE(dwell_required_s, :req) THEN 'verified' ELSE status END
        WHERE id=:sid
    """), {
        "llat": lat, "llng": lng, "acc": accuracy_m, "sid": session_id,
        "dwell": new_dwell, "req": settings.verify_dwell_required_s,
    })
    db.commit()

    if new_dwell >= int(row.get("dwell_required_s") or settings.verify_dwell_required_s):
        # Call reward logic (idempotent)
        rewarded = False
        wallet_delta = 0
        pool_delta = 0
        try:
            from app.services.rewards import award_verify_bonus
            ar = award_verify_bonus(db,
                user_id=int(row.get("user_id") or 0),
                session_id=session_id,
                amount=int(getattr(settings, 'verify_reward_cents', 200)),
                now=datetime.utcnow(),
            )
            rewarded = bool(ar.get("awarded"))
            wallet_delta = int(ar.get("user_delta") or 0)
            pool_delta = int(ar.get("pool_delta") or 0)
            logger.info({"at":"verify","step":"reward","sid":session_id,"uid":int(row.get("user_id") or 0),"gross":int(getattr(settings,'verify_reward_cents',200)),"net":wallet_delta,"pool":pool_delta,"ok":True})
        except Exception as e:
            logger.info({"at": "verify", "step": "reward", "sid": session_id, "err": str(e)})
        return {"ok": True, "verified": True, "rewarded": rewarded, "reward_cents": int(getattr(settings,'verify_reward_cents',200)), "wallet_delta_cents": wallet_delta, "pool_delta_cents": pool_delta, "dwell_seconds": new_dwell, "ping_count": int((row.get("ping_count") or 0) + 1)}

    resp = {
        "ok": True,
        "verified": False,
        "dwell_seconds": new_dwell,
        "distance_m": round(distance_m, 1),
        "needed_seconds": int(row.get("dwell_required_s") or settings.verify_dwell_required_s) - new_dwell,
        "accuracy_m": accuracy_m,
        "ping_count": int((row.get("ping_count") or 0) + 1),
    }
    if locals().get('acquired'):
        resp["target_acquired"] = True
    return resp


