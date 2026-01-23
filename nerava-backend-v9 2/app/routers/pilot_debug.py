"""
Pilot Debug API Router

Debug endpoints for onsite tuning at the Domain Hub.
Provides detailed verification metrics and scoring breakdowns.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import json

from app.db import get_db
from app.config import settings
from app.utils.log import get_logger

router = APIRouter(prefix="/v1/pilot/debug", tags=["pilot-debug"])
logger = get_logger(__name__)


def require_debug_token(x_debug_token: Optional[str] = Header(None)) -> bool:
    """Require X-Debug-Token header or environment flag for debug endpoints."""
    # In pilot mode, debug endpoints should be restricted
    if getattr(settings, "pilot_mode", True):
        # Still allow if DEBUG_MODE is enabled
        debug_enabled = getattr(settings, "DEBUG_MODE", False)
        if not debug_enabled:
            raise HTTPException(status_code=403, detail="Debug endpoints disabled in pilot mode")
    
    # Check environment flag
    debug_enabled = getattr(settings, "DEBUG_MODE", False)
    if debug_enabled:
        return True
    
    # Check header token
    expected_token = getattr(settings, "DEBUG_TOKEN", "domain-pilot-2024")
    if not x_debug_token:
        raise HTTPException(status_code=401, detail="Missing X-Debug-Token header")
    
    if x_debug_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid debug token")
    
    return True


@router.get("/session/{session_id}")
def debug_session(
    session_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_debug_token)
):
    """
    Get detailed debug information for a session.
    
    Returns:
    - Raw session pings
    - Distances computed
    - Penalties applied
    - Verification score breakdown
    - Chosen merchant/charger radius
    - Drift calculations
    """
    # Get session data (handle missing columns gracefully)
    try:
        session_row = db.execute(text("""
            SELECT 
                id, user_id, status, target_type, target_id, target_name,
                radius_m, started_lat, started_lng, last_lat, last_lng,
                min_accuracy_m, dwell_required_s, dwell_seconds, ping_count,
                created_at
            FROM sessions
            WHERE id = :session_id
        """), {"session_id": session_id}).mappings().first()
    except Exception:
        # Fallback to minimal columns
        session_row = db.execute(text("""
            SELECT 
                id, user_id, status, target_type, target_id, target_name,
                radius_m, started_lat, started_lng, last_lat, last_lng,
                dwell_required_s, dwell_seconds, ping_count
            FROM sessions
            WHERE id = :session_id
        """), {"session_id": session_id}).mappings().first()
    
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_dict = dict(session_row)
    
    # Get hub_id
    hub_id = None
    try:
        result = db.execute(text("SELECT hub_id FROM sessions WHERE id=:sid"), {"sid": session_id}).first()
        if result and result[0]:
            hub_id = str(result[0])
    except Exception:
        pass
    
    if not hub_id:
        # Try meta JSON
        meta = session_dict.get("meta")
        if meta:
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if isinstance(meta, dict) and "hub_id" in meta:
                hub_id = str(meta["hub_id"])
    
    # Parse ping history from meta (if column exists)
    ping_history = []
    try:
        meta_result = db.execute(text("SELECT meta FROM sessions WHERE id=:sid"), {"sid": session_id}).first()
        if meta_result and meta_result[0]:
            meta = meta_result[0]
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if isinstance(meta, dict) and "ping_history" in meta:
                ping_history = meta["ping_history"]
    except Exception:
        pass  # Meta column doesn't exist
    
    # Get target coordinates
    target_info = None
    target_type = session_dict.get("target_type")
    target_id = session_dict.get("target_id")
    
    if target_type and target_id:
        target_lat = None
        target_lng = None
        radius_used = session_dict.get("radius_m")
        
        # Get domain-specific radius if Domain hub
        if hub_id == "domain":
            try:
                from app.domains.domain_verification import (
                    get_charger_radius, get_merchant_radius
                )
                if target_type == "charger":
                    radius_used = get_charger_radius(target_id)
                elif target_type == "merchant":
                    radius_used = get_merchant_radius(target_id)
            except Exception:
                pass
        
        # Load target coordinates
        if target_type == "charger":
            result = db.execute(text("""
                SELECT lat, lng FROM chargers_openmap WHERE id=:id
            """), {"id": target_id}).first()
            if not result:
                result = db.execute(text("""
                    SELECT lat, lng FROM chargers WHERE id=:id
                """), {"id": target_id}).first()
            if result:
                target_lat = float(result[0])
                target_lng = float(result[1])
        elif target_type == "merchant":
            result = db.execute(text("""
                SELECT lat, lng FROM merchants WHERE id=:id
            """), {"id": target_id}).first()
            if result:
                target_lat = float(result[0])
                target_lng = float(result[1])
        
        if target_lat and target_lng:
            target_info = {
                "type": target_type,
                "id": target_id,
                "name": session_dict.get("target_name"),
                "lat": target_lat,
                "lng": target_lng,
                "radius_m": radius_used
            }
    
    # Calculate current distance if we have target and last position
    current_distance = None
    if target_info and session_dict.get("last_lat") and session_dict.get("last_lng"):
        from app.services.verify_dwell import haversine_m
        current_distance = haversine_m(
            session_dict["last_lat"], session_dict["last_lng"],
            target_info["lat"], target_info["lng"]
        )
    
    # Calculate drift from ping history
    drift_info = None
    if len(ping_history) >= 2:
        try:
            from datetime import datetime
            from app.services.verify_dwell import haversine_m
            from app.domains.domain_verification import DOMAIN_DRIFT_WINDOW_S, DOMAIN_DRIFT_TOLERANCE_M
            
            # Get last two pings
            last_ping = ping_history[-1]
            prev_ping = ping_history[-2] if len(ping_history) > 1 else None
            
            if prev_ping:
                last_ts = datetime.fromisoformat(last_ping["ts"]) if isinstance(last_ping["ts"], str) else last_ping["ts"]
                prev_ts = datetime.fromisoformat(prev_ping["ts"]) if isinstance(prev_ping["ts"], str) else prev_ping["ts"]
                time_delta = (last_ts - prev_ts).total_seconds()
                
                if time_delta <= DOMAIN_DRIFT_WINDOW_S:
                    drift_m = haversine_m(
                        last_ping["lat"], last_ping["lng"],
                        prev_ping["lat"], prev_ping["lng"]
                    )
                    
                    drift_info = {
                        "drift_m": round(drift_m, 1),
                        "time_delta_s": round(time_delta, 1),
                        "within_tolerance": drift_m <= DOMAIN_DRIFT_TOLERANCE_M,
                        "tolerance_m": DOMAIN_DRIFT_TOLERANCE_M
                    }
        except Exception as e:
            logger.debug(f"Could not calculate drift: {str(e)}")
    
    # Build response
    response = {
        "session_id": session_id,
        "hub_id": hub_id,
        "status": session_dict.get("status"),
        "target": target_info,
        "current_distance_m": round(current_distance, 1) if current_distance else None,
        "radius_m": session_dict.get("radius_m"),
        "dwell_seconds": session_dict.get("dwell_seconds", 0),
        "dwell_required_s": session_dict.get("dwell_required_s"),
        "ping_count": session_dict.get("ping_count", 0),
        "ping_history": ping_history[-10:],  # Last 10 pings
        "last_position": {
            "lat": session_dict.get("last_lat"),
            "lng": session_dict.get("last_lng"),
            "accuracy_m": session_dict.get("last_accuracy_m")
        },
        "drift_info": drift_info,
        "started_at": session_dict.get("created_at").isoformat() if session_dict.get("created_at") else None
    }
    
    return response

