"""
Pilot API Router

Domain Pilot Driver Flow - End-to-End API for the Domain Hub pilot.
Provides a cohesive, PWA-optimized API layer for the pilot PWA.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.db import get_db
from app.models import User
from app.dependencies.domain import require_merchant_admin
from app.dependencies.driver import get_current_driver
from app.services.auth_service import AuthService
from app.domains.domain_hub import HUB_ID, HUB_NAME, DOMAIN_CHARGERS
from app.services.verify_dwell import start_session as verify_start_session, ping as verify_ping
from app.services.while_you_charge import get_domain_hub_view, get_domain_hub_view_async
from app.services.rewards import award_verify_bonus
from app.services.nova import cents_to_nova
from app.services.verify_dwell import haversine_m
from app.utils.pwa_responses import (
    normalize_number, shape_charger, shape_merchant, shape_error
)
from app.config import settings
from app.utils.log import get_logger
from app.services.codes import generate_code, store_code, fetch_code, is_code_valid

router = APIRouter(prefix="/v1/pilot", tags=["pilot"])
logger = get_logger(__name__)


# Request/Response Models
class StartSessionRequest(BaseModel):
    user_lat: float
    user_lng: float
    charger_id: Optional[str] = None  # Optional: specific charger to use
    merchant_id: Optional[str] = None  # Optional: selected merchant for the session


class VerifyPingRequest(BaseModel):
    session_id: str
    user_lat: float
    user_lng: float


class VerifyVisitRequest(BaseModel):
    session_id: str
    merchant_id: str
    user_lat: float
    user_lng: float


class CancelSessionRequest(BaseModel):
    session_id: str


# Error handling will be done at the app level via middleware


# ============================================
# Endpoint 1: POST /v1/pilot/start_session
# DEPRECATED: Use /v1/drivers/charge_events/{event_slug}/join instead
# ============================================
@router.post("/start_session", deprecated=True)
def start_session(
    request: StartSessionRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Start a charging session for the Domain hub.
    
    Creates a session associated with hub "domain", stores location,
    and returns session info with nearest charger.
    PWA-optimized: clean response shape, integers only, no internal fields.
    """
    session_id = str(uuid.uuid4())
    
    # Use provided charger_id or find nearest Domain charger
    selected_charger_config = None
    if request.charger_id:
        # Find specific charger from config
        for charger_config in DOMAIN_CHARGERS:
            if charger_config["id"] == request.charger_id:
                selected_charger_config = charger_config
                break
        if not selected_charger_config:
            raise HTTPException(status_code=404, detail=f"Charger {request.charger_id} not found")
    else:
        # Find nearest Domain charger
        min_distance = float('inf')
        for charger_config in DOMAIN_CHARGERS:
            distance = haversine_m(
                request.user_lat, request.user_lng,
                charger_config["lat"], charger_config["lng"]
            )
            if distance < min_distance:
                min_distance = distance
                selected_charger_config = charger_config
    
    # Shape charger for PWA
    if selected_charger_config:
        nearest_charger = shape_charger(
            {
                "id": selected_charger_config["id"],
                "name": selected_charger_config["name"],
                "lat": selected_charger_config["lat"],
                "lng": selected_charger_config["lng"],
                "network_name": selected_charger_config.get("network_name"),
            },
            user_lat=request.user_lat,
            user_lng=request.user_lng
        )
    else:
        raise HTTPException(status_code=500, detail="No Domain chargers found")
    
    # Get merchant info if merchant_id provided
    merchant_info = None
    if request.merchant_id:
        merchant_row = db.execute(text("""
            SELECT m.id, m.name, m.lat, m.lng,
                   COALESCE(mp.nova_reward, 10) as nova_reward,
                   cm.walk_duration_s, cm.walk_distance_m, cm.distance_m
            FROM merchants m
            LEFT JOIN merchant_perks mp ON mp.merchant_id = m.id AND mp.is_active = 1
            LEFT JOIN charger_merchants cm ON cm.merchant_id = m.id AND cm.charger_id = :charger_id
            WHERE m.id = :merchant_id
            LIMIT 1
        """), {"merchant_id": request.merchant_id, "charger_id": selected_charger_config["id"]}).first()
        
        if merchant_row:
            merchant_info = {
                "id": merchant_row[0],
                "name": merchant_row[1],
                "lat": float(merchant_row[2]),
                "lng": float(merchant_row[3]),
                "nova_reward": normalize_number(merchant_row[4] or 10),
                "walk_time_s": normalize_number(merchant_row[5] or 0),
                "walk_distance_m": normalize_number(merchant_row[6] or 0),
                "distance_m": normalize_number(merchant_row[7] or 0),
                "required_charger_radius_m": normalize_number(selected_charger_config.get("radius_m", 60)),
                "required_dwell_s": normalize_number(180),  # 3 minutes default
                "required_merchant_radius_m": normalize_number(100)  # 100m default
            }
            
            # Store merchant_id in session meta for later reference
            try:
                db.execute(text("""
                    UPDATE sessions
                    SET meta = json_set(COALESCE(meta, '{}'), '$.merchant_id', :merchant_id)
                    WHERE id = :session_id
                """), {"merchant_id": request.merchant_id, "session_id": session_id})
            except Exception:
                pass  # Ignore if JSON functions not available
    
    # Create session in sessions table with hub_id in meta
    now = datetime.utcnow()
    
    try:
        # First ensure session exists (verify_dwell uses UPDATE, so create if needed)
        existing = db.execute(text("""
            SELECT id FROM sessions WHERE id = :session_id
        """), {"session_id": session_id}).first()
        
        if not existing:
            # Create session row first
            db.execute(text("""
                INSERT INTO sessions (id, user_id, status, started_at, created_at)
                VALUES (:id, :user_id, 'pending', :started_at, :created_at)
            """), {
                "id": session_id,
                "user_id": user_id,
                "started_at": now,
                "created_at": now
            })
            db.commit()
        
        # Use verify_dwell's start_session which handles target selection
        result = verify_start_session(
            db=db,
            session_id=session_id,
            user_id=user_id,
            lat=request.user_lat,
            lng=request.user_lng,
            accuracy_m=50.0,  # Default accuracy for pilot
            ua="Pilot-PWA",
            event_id=None
        )
        
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result.get("reason", "Failed to start session"))
        
        # Store hub_id in session meta (or update if meta column exists)
        try:
            db.execute(text("""
                UPDATE sessions
                SET hub_id = :hub_id
                WHERE id = :session_id
            """), {"hub_id": HUB_ID, "session_id": session_id})
        except Exception:
            # If hub_id column doesn't exist, store in meta JSON
            try:
                db.execute(text("""
                    UPDATE sessions
                    SET meta = json_set(COALESCE(meta, '{}'), '$.hub_id', :hub_id)
                    WHERE id = :session_id
                """), {"hub_id": HUB_ID, "session_id": session_id})
            except Exception:
                # If JSON functions not available, just log
                logger.warning(f"Could not set hub_id for session {session_id}")
        
        db.commit()
        
        # PWA-optimized response: clean shape, integers only
        response = {
            "session_id": session_id,
            "hub_id": HUB_ID,
            "hub_name": HUB_NAME,
            "charger": nearest_charger,
            "status": result.get("status", "started"),
            "dwell_required_s": normalize_number(result.get("dwell_required_s", 180)),
            "min_accuracy_m": normalize_number(result.get("min_accuracy_m", 50))
        }
        
        # Add merchant info if provided
        if merchant_info:
            response["merchant"] = merchant_info
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to start pilot session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


# ============================================
# Endpoint 2: POST /v1/pilot/verify_ping
# DEPRECATED: Use /v1/drivers/sessions/{id}/ping instead
# ============================================
@router.post("/verify_ping", deprecated=True)
def verify_ping_endpoint(
    request: VerifyPingRequest,
    db: Session = Depends(get_db)
):
    """
    Periodic GPS ping for session verification.
    
    Calls existing verify engine, updates session events.
    If verification threshold met, triggers reward issuance.
    PWA-optimized: includes reward_earned flag, integers only.
    """
    print(f"[PilotRouter][verify_ping] Endpoint called: session_id={request.session_id}, lat={request.user_lat}, lng={request.user_lng}", flush=True)
    try:
        result = verify_ping(
            db=db,
            session_id=request.session_id,
            lat=request.user_lat,
            lng=request.user_lng,
            accuracy_m=50.0  # Default accuracy for pilot
        )
        
        print(f"[PilotRouter][verify_ping] verify_ping result: {result}", flush=True)
        
        if not result.get("ok"):
            reason = result.get("reason", "Verification failed")
            print(f"[PilotRouter][verify_ping] Verification failed: {reason}", flush=True)
            raise HTTPException(status_code=400, detail=reason)
        
        # Get session info to retrieve user_id and wallet balance
        session_row = db.execute(text("""
            SELECT user_id, status FROM sessions WHERE id = :session_id
        """), {"session_id": request.session_id}).first()
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_id = session_row[0]
        is_verified = result.get("verified", False)
        is_rewarded = is_verified and result.get("rewarded", False)
        
        # Get wallet balance (handle case where credit_ledger table doesn't exist yet)
        wallet_balance_cents = 0
        try:
            from app.models_extra import CreditLedger
            ledger_rows = db.query(CreditLedger).filter(CreditLedger.user_ref == str(user_id)).all()
            wallet_balance_cents = sum(r.cents for r in ledger_rows) if ledger_rows else 0
        except Exception as ledger_err:
            # Table might not exist yet - return 0 balance
            logger.warning(f"Could not query wallet balance (table may not exist): {ledger_err}")
            print(f"[PilotRouter][verify_ping] Warning: Could not query wallet balance: {ledger_err}", flush=True)
            wallet_balance_cents = 0
        
        # Get session merchant_id from meta if available
        merchant_id = None
        try:
            session_meta = db.execute(text("""
                SELECT meta FROM sessions WHERE id = :session_id
            """), {"session_id": request.session_id}).first()
            if session_meta and session_meta[0]:
                import json
                meta = session_meta[0] if isinstance(session_meta[0], dict) else json.loads(session_meta[0])
                merchant_id = meta.get("merchant_id") if isinstance(meta, dict) else None
        except Exception:
            pass
        
        # Calculate distance to charger
        charger_row = db.execute(text("""
            SELECT target_id FROM sessions WHERE id = :session_id
        """), {"session_id": request.session_id}).first()
        charger_id = charger_row[0] if charger_row else None
        
        distance_to_charger_m = normalize_number(result.get("distance_m", 0))
        charger_radius_m = normalize_number(result.get("radius_m", 60))
        verified_at_charger = is_verified
        
        # Calculate distance to merchant if merchant_id exists
        distance_to_merchant_m = None
        within_merchant_radius = False
        if merchant_id:
            try:
                merchant_row = db.execute(text("""
                    SELECT lat, lng FROM merchants WHERE id = :merchant_id
                """), {"merchant_id": merchant_id}).first()
                if merchant_row:
                    merchant_lat = float(merchant_row[0])
                    merchant_lng = float(merchant_row[1])
                    distance_to_merchant_m = normalize_number(haversine_m(
                        request.user_lat, request.user_lng,
                        merchant_lat, merchant_lng
                    ))
                    within_merchant_radius = distance_to_merchant_m <= 100  # 100m default radius
                else:
                    # Merchant not found in DB (might be a fallback merchant) - skip distance calculation
                    logger.debug(f"Merchant {merchant_id} not found in DB, skipping distance calculation")
            except Exception as merchant_err:
                # If merchants table doesn't exist or query fails, skip merchant distance calculation
                logger.warning(f"Failed to query merchant distance: {merchant_err}")
                # Continue without merchant distance - not critical for verification
        
        # PWA-optimized response: clean shape, integers only, reward_earned flag
        response = {
            "verified": is_verified,
            "reward_earned": is_rewarded,  # Flag for PWA to trigger notifications
            "verified_at_charger": verified_at_charger,
            "distance_to_charger_m": distance_to_charger_m,
            "dwell_seconds": normalize_number(result.get("dwell_seconds", 0)),
            "verification_score": normalize_number(result.get("verification_score", 100 if is_verified else 0)),
            "wallet_balance": wallet_balance_cents,
            "wallet_balance_nova": cents_to_nova(wallet_balance_cents),
            "ready_to_claim": is_verified and not is_rewarded,  # Ready to claim when verified but not yet rewarded
        }
        
        # Add merchant distance if merchant_id exists
        if distance_to_merchant_m is not None:
            response["distance_to_merchant_m"] = distance_to_merchant_m
            response["within_merchant_radius"] = within_merchant_radius
        
        # Add charger radius info
        if charger_radius_m:
            response["charger_radius_m"] = charger_radius_m
        
        # Add score components if available (keep for debugging, but normalize numbers)
        if "score_components" in result:
            components = result["score_components"]
            response["score_components"] = {
                k: normalize_number(v) for k, v in components.items()
            }
        
        # If verified and rewarded, add Nova fields
        if is_rewarded:
            response["nova_awarded"] = cents_to_nova(result.get("reward_cents", 0))
            response["wallet_delta_cents"] = normalize_number(result.get("wallet_delta_cents", 0))
            response["wallet_delta_nova"] = cents_to_nova(result.get("wallet_delta_cents", 0))
            response["ready_to_claim"] = False  # Already claimed
        else:
            response["nova_awarded"] = 0
        
        # Add remaining needed time if not verified
        if not is_verified:
            needed = result.get("needed_seconds", 0)
            response["needed_seconds"] = normalize_number(needed)
        
        # Add drift info if available (normalize)
        if "drift_m" in result:
            response["drift_m"] = normalize_number(result["drift_m"])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Failed to verify ping: {str(e)}\n{error_trace}")
        print(f"[PilotRouter][ERROR] verify_ping failed: {str(e)}", flush=True)
        print(f"[PilotRouter][ERROR] Traceback: {error_trace}", flush=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


# ============================================
# Endpoint 3: GET /v1/pilot/while_you_charge
# DEPRECATED: Use /v1/drivers/merchants/nearby instead
# ============================================
@router.get("/while_you_charge", deprecated=True)
async def while_you_charge(
    session_id: Optional[str] = Query(None, description="Optional session ID"),
    user_lat: Optional[float] = Query(None, description="Optional user latitude for distance calculation"),
    user_lng: Optional[float] = Query(None, description="Optional user longitude for distance calculation"),
    db: Session = Depends(get_db)
):
    """
    Get Domain hub chargers and recommended merchants.
    
    Returns chargers and merchants for the Domain hub.
    PWA-optimized: consistent object shapes, no nulls, integers only.
    """
    # Explicit logging that will definitely show up (print goes to stderr which Railway captures)
    print("[WhileYouCharge][API] ====== ENDPOINT CALLED ======", flush=True)
    logger.info("[WhileYouCharge][API] ====== ENDPOINT CALLED ======")
    
    try:
        print(f"[WhileYouCharge][API] About to call get_domain_hub_view_async...", flush=True)
        logger.info("[WhileYouCharge][API] About to call get_domain_hub_view_async...")
        
        # Use async version to properly handle merchant fetching
        hub_view = await get_domain_hub_view_async(db)
        
        print(f"[WhileYouCharge][API] Got hub_view: {hub_view.get('hub_id')} with {len(hub_view.get('chargers', []))} chargers", flush=True)
        
        raw_merchants = hub_view.get("merchants", [])
        chargers_in_view = hub_view.get("chargers", [])
        
        print(f"[WhileYouCharge][API] Hub view: {len(chargers_in_view)} chargers, {len(raw_merchants)} raw merchants", flush=True)
        logger.info(f"[WhileYouCharge][API] Hub view: {len(chargers_in_view)} chargers, {len(raw_merchants)} raw merchants")
        
        # Check if chargers have merchants attached
        total_merchants_in_chargers = sum(len(ch.get("merchants", [])) for ch in chargers_in_view)
        print(f"[WhileYouCharge][API] Total merchants attached to chargers: {total_merchants_in_chargers}", flush=True)
        logger.info(f"[WhileYouCharge][API] Total merchants attached to chargers: {total_merchants_in_chargers}")
        
        if not raw_merchants and total_merchants_in_chargers == 0:
            print(f"[WhileYouCharge][API] ⚠️ WARNING: No merchants found! Raw merchants: {len(raw_merchants)}, In chargers: {total_merchants_in_chargers}", flush=True)
            logger.warning(f"[WhileYouCharge][API] ⚠️ No merchants in hub_view! Raw: {len(raw_merchants)}, In chargers: {total_merchants_in_chargers}")
        
        # Shape chargers for PWA (merchants are already attached in hub_view)
        shaped_chargers = []
        print(f"[WhileYouCharge][API] Shaping {len(chargers_in_view)} chargers...", flush=True)
        
        for charger in chargers_in_view:
            charger_id = charger.get("id", "unknown")
            # Get merchants array from charger (if attached)
            charger_merchants = charger.get("merchants", [])
            
            print(f"[WhileYouCharge][API] Charger {charger_id} has {len(charger_merchants)} merchants attached", flush=True)
            
            shaped = shape_charger(
                charger,
                user_lat=user_lat,
                user_lng=user_lng
            )
            # Shape merchants attached to this charger
            shaped_merchants_for_charger = []
            for merchant in charger_merchants:
                # Convert walk_minutes to walk_time_s if needed
                if "walk_minutes" in merchant and "walk_time_s" not in merchant:
                    merchant["walk_time_s"] = merchant["walk_minutes"] * 60
                shaped_merchant = shape_merchant(
                    merchant,
                    user_lat=user_lat,
                    user_lng=user_lng
                )
                # Ensure walk_time_seconds for aggregation
                if "walk_time_s" in shaped_merchant:
                    shaped_merchant["walk_time_seconds"] = shaped_merchant["walk_time_s"]
                elif "walk_minutes" in merchant:
                    shaped_merchant["walk_time_seconds"] = normalize_number(merchant["walk_minutes"] * 60)
                # Ensure merchant_id for aggregation
                if "id" in shaped_merchant and "merchant_id" not in shaped_merchant:
                    shaped_merchant["merchant_id"] = shaped_merchant["id"]
                shaped_merchants_for_charger.append(shaped_merchant)
            
            # Attach shaped merchants to charger
            shaped["merchants"] = shaped_merchants_for_charger
            shaped_chargers.append(shaped)
            logger.info(
                "[WhileYouCharge][API] Charger %s shaped with %d merchants",
                shaped.get("id"),
                len(shaped_merchants_for_charger),
            )
        
        # Build recommended_merchants from charger merchants
        hub_id = hub_view.get("hub_id")
        hub_name = hub_view.get("hub_name")
        
        print(f"[WhileYouCharge][API] Building recommended_merchants for hub_id={hub_id} from {len(shaped_chargers)} chargers", flush=True)
        logger.info(
            "[WhileYouCharge][API] Building recommended_merchants for hub_id=%s from %d chargers",
            hub_id,
            len(shaped_chargers),
        )
        
        from app.services.while_you_charge import build_recommended_merchants_from_chargers
        recommended_merchants = build_recommended_merchants_from_chargers(shaped_chargers, limit=20)
        
        # Fallback to default merchants if none found (for testing user flow)
        if len(recommended_merchants) == 0:
            print(f"[WhileYouCharge][API] ⚠️ No real merchants found, using default fallback merchants", flush=True)
            logger.warning("[WhileYouCharge][API] No real merchants found, using default fallback merchants")
            
            # Default merchants at Domain hub location (30.4019, -97.7251)
            default_merchants = [
                {
                    "id": "merchant_starbucks_domain",
                    "merchant_id": "merchant_starbucks_domain",
                    "name": "Starbucks",
                    "logo_url": "https://logo.clearbit.com/starbucks.com",
                    "lat": 30.4020,
                    "lng": -97.7250,
                    "category": "coffee",
                    "nova_reward": 12,
                    "walk_time_seconds": 180,  # 3 minutes
                    "walk_time_s": 180,
                    "walk_minutes": 3,
                    "distance_m": 150,
                },
                {
                    "id": "merchant_target_domain",
                    "merchant_id": "merchant_target_domain",
                    "name": "Target",
                    "logo_url": "https://logo.clearbit.com/target.com",
                    "lat": 30.4018,
                    "lng": -97.7248,
                    "category": "retail",
                    "nova_reward": 8,
                    "walk_time_seconds": 300,  # 5 minutes
                    "walk_time_s": 300,
                    "walk_minutes": 5,
                    "distance_m": 250,
                },
                {
                    "id": "merchant_wholefoods_domain",
                    "merchant_id": "merchant_wholefoods_domain",
                    "name": "Whole Foods",
                    "logo_url": "https://logo.clearbit.com/wholefoodsmarket.com",
                    "lat": 30.4017,
                    "lng": -97.7252,
                    "category": "grocery",
                    "nova_reward": 10,
                    "walk_time_seconds": 420,  # 7 minutes
                    "walk_time_s": 420,
                    "walk_minutes": 7,
                    "distance_m": 350,
                }
            ]
            recommended_merchants = default_merchants
        
        print(f"[WhileYouCharge][API] FINAL: chargers={len(shaped_chargers)}, recommended_merchants={len(recommended_merchants)}", flush=True)
        logger.info(
            "[WhileYouCharge][API] WhileYouCharge response: chargers=%d, recommended_merchants=%d",
            len(shaped_chargers),
            len(recommended_merchants),
        )
        
        return {
            "hub_id": hub_id,
            "hub_name": hub_name,
            "chargers": shaped_chargers,
            "recommended_merchants": recommended_merchants
        }
    except Exception as e:
        logger.error(f"Failed to get Domain hub view: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load hub data: {str(e)}")


# ============================================
# Endpoint 4: POST /v1/pilot/verify_visit
# ============================================
@router.post("/verify_visit")
def verify_visit(
    request: VerifyVisitRequest,
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Verify merchant visit and award Nova.
    
    Runs visit-verification, awards merchant visit Nova if valid,
    and updates wallet.
    PWA-optimized: includes reward_earned flag, integers only.
    
    P0-1 Security: Requires authentication. Mutates wallet balance.
    """
    # Get merchant info (handle fallback merchants that may not be in DB)
    merchant = None
    merchant_lat = None
    merchant_lng = None
    
    try:
        merchant = db.execute(text("""
            SELECT id, name, lat, lng FROM merchants WHERE id = :merchant_id
        """), {"merchant_id": request.merchant_id}).first()
        
        if merchant:
            merchant_lat = float(merchant[2])
            merchant_lng = float(merchant[3])
        else:
            # Merchant not in DB - might be a fallback merchant
            # Use default coordinates near Domain hub (30.4019, -97.7251)
            # Fallback merchants are positioned around Domain hub
            print(f"[PilotRouter][verify_visit] Merchant {request.merchant_id} not found in DB, using fallback coordinates", flush=True)
            logger.warning(f"Merchant {request.merchant_id} not found in DB, using fallback coordinates")
            merchant_lat = 30.4020  # Near Domain hub
            merchant_lng = -97.7250
    except Exception as merchant_err:
        # If merchants table doesn't exist or query fails, use fallback coordinates
        logger.warning(f"Could not query merchant (table may not exist): {merchant_err}")
        print(f"[PilotRouter][verify_visit] Could not query merchant, using fallback coordinates: {merchant_err}", flush=True)
        merchant_lat = 30.4020
        merchant_lng = -97.7250
    
    # Check distance (within 100m radius)
    distance_m = haversine_m(
        request.user_lat, request.user_lng,
        merchant_lat, merchant_lng
    )
    
    # P0-1: Use authenticated user ID instead of session user_id
    authenticated_user_id = user.id
    
    # Verify session exists and belongs to authenticated user
    session_row = db.execute(text("""
        SELECT user_id FROM sessions WHERE id = :session_id
    """), {"session_id": request.session_id}).first()
    
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_user_id = session_row[0]
    
    # P0-1: Ensure session belongs to authenticated user
    if session_user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="Session does not belong to authenticated user"
        )
    
    if distance_m > 100:
        # Get wallet balance even if too far
        # Get wallet balance (handle case where credit_ledger table doesn't exist yet)
        wallet_balance_cents = 0
        try:
            from app.models_extra import CreditLedger
            ledger_rows = db.query(CreditLedger).filter(CreditLedger.user_ref == str(authenticated_user_id)).all()
            wallet_balance_cents = sum(r.cents for r in ledger_rows) if ledger_rows else 0
        except Exception as ledger_err:
            # Table might not exist yet - return 0 balance
            logger.warning(f"Could not query wallet balance (table may not exist): {ledger_err}")
            wallet_balance_cents = 0
        
        return {
            "verified": False,
            "reward_earned": False,
            "reason": "too_far",
            "distance_m": normalize_number(distance_m),
            "nova_awarded": 0,
            "wallet_balance": wallet_balance_cents,
            "wallet_balance_nova": cents_to_nova(wallet_balance_cents)
        }
    
    user_id = authenticated_user_id
    
    # Check if visit already rewarded (idempotency)
    existing_reward = db.execute(text("""
        SELECT id FROM reward_events
        WHERE user_id = :user_id
        AND source = 'merchant_visit'
        AND meta LIKE :pattern
        LIMIT 1
    """), {
        "user_id": str(authenticated_user_id),
        "pattern": f'%{request.merchant_id}%'
    }).first()
    
    if existing_reward:
        # Return existing state (already rewarded)
        # Get wallet balance (handle case where credit_ledger table doesn't exist yet)
        wallet_balance_cents = 0
        try:
            from app.models_extra import CreditLedger
            ledger_rows = db.query(CreditLedger).filter(CreditLedger.user_ref == str(user_id)).all()
            wallet_balance_cents = sum(r.cents for r in ledger_rows) if ledger_rows else 0
        except Exception as ledger_err:
            # Table might not exist yet - return 0 balance
            logger.warning(f"Could not query wallet balance (table may not exist): {ledger_err}")
            wallet_balance_cents = 0
        return {
            "verified": True,
            "reward_earned": False,  # Not newly earned
            "reason": "already_rewarded",
            "nova_awarded": 0,
            "wallet_balance": wallet_balance_cents,
            "wallet_balance_nova": cents_to_nova(wallet_balance_cents)
        }
    
    # Award merchant visit reward (25 Nova = 25 cents)
    visit_reward_cents = 25
    
    try:
        # Use similar logic to verify bonus but for merchant visit
        from app.utils.dbjson import as_db_json
        from app.db import get_engine

        meta_dict = {
            "merchant_id": request.merchant_id,
            "session_id": request.session_id,
            "type": "merchant_visit"
        }
        engine = get_engine()
        meta_json = as_db_json(meta_dict, engine)
        
        # Insert reward event
        db.execute(text("""
            INSERT INTO reward_events (
                user_id, source, gross_cents, net_cents, community_cents, meta, created_at
            ) VALUES (
                :user_id, 'merchant_visit', :gross, :net, :community, :meta, :created_at
            )
        """), {
            "user_id": str(authenticated_user_id),
            "gross": visit_reward_cents,
            "net": visit_reward_cents,  # Full amount to user for merchant visit
            "community": 0,
            "meta": meta_json,
            "created_at": datetime.utcnow()
        })
        
        # Update wallet
        from app.routers.wallet import _balance, _add_ledger
        new_balance = _add_ledger(
            db, str(authenticated_user_id), visit_reward_cents,
            "MERCHANT_VISIT", {"merchant_id": request.merchant_id, "session_id": request.session_id}
        )
        
        db.commit()
        
        # Generate/fetch merchant code for discount (skip if merchant doesn't exist in DB)
        merchant_code = None
        try:
            from app.services.codes import generate_code, store_code, fetch_code
            from app.models_while_you_charge import MerchantOfferCode
            
            # For fallback merchants, generate a simple code without DB lookup
            if not merchant:
                # Fallback merchant - generate a simple code
                merchant_code = f"DOM-{request.merchant_id[-4:].upper()}"
                print(f"[PilotRouter][verify_visit] Generated fallback code for merchant {request.merchant_id}: {merchant_code}", flush=True)
            else:
                # Try to fetch existing valid code for this merchant
                existing_code = db.query(MerchantOfferCode).filter(
                    MerchantOfferCode.merchant_id == request.merchant_id,
                    MerchantOfferCode.is_redeemed == False,
                    MerchantOfferCode.expires_at > datetime.utcnow()
            ).first()
            
            if existing_code:
                merchant_code = existing_code.code
            else:
                # Generate new code (1000 cents = $10 discount)
                offer_code = store_code(
                    db=db,
                    merchant_id=request.merchant_id,
                    amount_cents=1000,  # $10 default discount
                    expiration_days=30
                )
                merchant_code = offer_code.code
        except Exception as e:
            logger.warning(f"Could not generate merchant code: {e}")
            merchant_code = None  # Optional field - don't fail if code generation fails
        
        # PWA-optimized response
        return {
            "visit_verified": True,
            "verified": True,
            "reward_earned": True,  # Flag for PWA to trigger confetti
            "nova_awarded": cents_to_nova(visit_reward_cents),
            "wallet_balance": new_balance,
            "wallet_balance_nova": cents_to_nova(new_balance),
            "merchant_code": merchant_code  # Discount code for merchant
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to award merchant visit reward: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to award reward: {str(e)}")


# ============================================
# Endpoint 4.5: POST /v1/pilot/session/cancel
# DEPRECATED: Use /v1/drivers/sessions/{id}/cancel instead
# ============================================
@router.post("/session/cancel", deprecated=True)
def cancel_session(
    request: CancelSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel a pilot earn session.
    
    Marks the session as cancelled and prevents it from being eligible for rewards.
    Idempotent: safe to call multiple times.
    """
    session_id = request.session_id
    
    try:
        # Check if session exists and get its status
        session_row = db.execute(text("""
            SELECT status, user_id FROM sessions WHERE id = :session_id
        """), {"session_id": session_id}).first()
        
        if not session_row:
            # Session not found - return success anyway (idempotent)
            return {"ok": True, "message": "Session not found or already cancelled"}
        
        status = session_row[0]
        
        # If already cancelled or completed, return success (idempotent)
        if status in ("cancelled", "completed", "verified"):
            return {"ok": True, "message": f"Session already {status}"}
        
        # Update session status to cancelled
        # Handle case where cancelled_at column may not exist
        try:
            db.execute(text("""
                UPDATE sessions
                SET status = 'cancelled',
                    cancelled_at = :now
                WHERE id = :session_id
            """), {
                "session_id": session_id,
                "now": datetime.utcnow()
            })
        except Exception as col_err:
            # Fallback if cancelled_at column doesn't exist yet
            logger.warning(f"[PilotRouter][cancel] cancelled_at column may not exist: {col_err}")
            db.execute(text("""
                UPDATE sessions
                SET status = 'cancelled'
                WHERE id = :session_id
            """), {
                "session_id": session_id
            })
        
        db.commit()
        
        logger.info(f"[PilotRouter][cancel] Session {session_id} cancelled")
        
        return {"ok": True, "message": "Session cancelled"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"[PilotRouter][cancel] Failed to cancel session {session_id}: {e}", exc_info=True)
        # Return success anyway to avoid blocking UI cleanup
        return {"ok": True, "message": "Cancellation processed"}


# Endpoint 5: GET /v1/pilot/activity
# DEPRECATED: Use /v1/drivers/activity instead
# ============================================
@router.get("/activity", deprecated=True)
def get_activity(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return"),
    db: Session = Depends(get_db)
):
    """
    Get driver activity feed.
    
    Returns latest sessions, merchant visits, rewards, and Nova deltas.
    PWA-optimized: clean shapes, integers only, no internal IDs.
    """
    activities = []
    
    try:
        # Check if credit_ledger table exists before querying
        table_check = db.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='credit_ledger'
        """)).first()
        
        if table_check:
            # Get wallet ledger entries
            ledger_entries = db.execute(text("""
                SELECT cents, reason, meta, created_at
                FROM credit_ledger
                WHERE user_ref = :user_id
                ORDER BY id DESC
                LIMIT :limit
            """), {"user_id": user_id, "limit": limit}).fetchall()
        else:
            ledger_entries = []
    except Exception as e:
        logger.warning(f"[PilotRouter][activity] Credit ledger query failed: {e}")
        ledger_entries = []
    
    for entry in ledger_entries:
        # Shape for PWA: remove internal IDs, normalize numbers
        meta = entry[2] if isinstance(entry[2], dict) else {}
        # Remove internal fields from meta
        pwa_meta = {}
        if isinstance(meta, dict):
            # Only keep merchant_id, session_id if present
            if "merchant_id" in meta:
                pwa_meta["merchant_id"] = str(meta["merchant_id"])
            if "session_id" in meta:
                pwa_meta["session_id"] = str(meta["session_id"])
        
        activities.append({
            "type": "wallet",
            "nova_delta": cents_to_nova(entry[0]),  # Primary field for PWA
            "cents": normalize_number(entry[0]),
            "reason": entry[1] or "",
            "meta": pwa_meta,
            "ts": entry[3].isoformat() if isinstance(entry[3], datetime) else str(entry[3])
        })
    
    # Get reward events (if table exists)
    try:
        table_check = db.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='reward_events'
        """)).first()
        
        if table_check:
            reward_events = db.execute(text("""
                SELECT source, gross_cents, meta, created_at
                FROM reward_events
                WHERE user_id = :user_id
                ORDER BY id DESC
                LIMIT :limit
            """), {"user_id": user_id, "limit": limit}).fetchall()
        else:
            reward_events = []
    except Exception as e:
        logger.warning(f"[PilotRouter][activity] Reward events query failed: {e}")
        reward_events = []
    
    for event in reward_events:
        # Shape for PWA: remove internal IDs
        meta = event[2] if isinstance(event[2], dict) else {}
        pwa_meta = {}
        if isinstance(meta, dict):
            if "merchant_id" in meta:
                pwa_meta["merchant_id"] = str(meta["merchant_id"])
            if "session_id" in meta:
                pwa_meta["session_id"] = str(meta["session_id"])
        
        reward_activity = {
            "type": "reward",
            "source": event[0],
            "nova_awarded": cents_to_nova(event[1]),  # Primary field for PWA
            "gross_cents": normalize_number(event[1]),
            "meta": pwa_meta,
            "ts": event[3].isoformat() if isinstance(event[3], datetime) else str(event[3])
        }
        
        # Add merchant_name if merchant_id is in meta
        if isinstance(meta, dict) and "merchant_id" in meta:
            merchant_name_row = db.execute(text("""
                SELECT name FROM merchants WHERE id = :merchant_id
            """), {"merchant_id": meta["merchant_id"]}).first()
            if merchant_name_row:
                reward_activity["merchant_name"] = merchant_name_row[0]
        
        activities.append(reward_activity)
    
    # Get sessions with merchant info (simplified for PWA)
    try:
        table_check = db.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'
        """)).first()
        
        if table_check:
            sessions = db.execute(text("""
                SELECT s.id, s.status, s.target_id, s.meta,
                       c.name as charger_name,
                       m.name as merchant_name
                FROM sessions s
                LEFT JOIN chargers c ON c.id = s.target_id
                LEFT JOIN merchants m ON json_extract(s.meta, '$.merchant_id') = m.id
                WHERE s.user_id = :user_id
                ORDER BY s.id DESC
                LIMIT :limit
            """), {"user_id": int(user_id) if user_id.isdigit() else 0, "limit": min(limit, 10)}).fetchall()
        else:
            sessions = []
    except Exception as e:
        logger.warning(f"[PilotRouter][activity] Sessions query failed: {e}")
        sessions = []
    
    for session in sessions:
        session_activity = {
            "type": "session",
            "session_id": session[0],
            "status": session[1],
            "charger_name": session[4] or "Unknown Charger",
        }
        
        # Add merchant_name if available
        if session[5]:  # merchant_name
            session_activity["merchant_name"] = session[5]
        
        # Try to get hub_id from meta or target_id
        try:
            if session[3]:  # meta
                import json
                meta = session[3] if isinstance(session[3], dict) else json.loads(session[3] or "{}")
                if isinstance(meta, dict):
                    if "hub_id" in meta:
                        session_activity["hub_id"] = str(meta["hub_id"])
                    if "merchant_id" in meta and not session[5]:
                        # Fetch merchant name if not already joined
                        merchant_name_row = db.execute(text("""
                            SELECT name FROM merchants WHERE id = :merchant_id
                        """), {"merchant_id": meta["merchant_id"]}).first()
                        if merchant_name_row:
                            session_activity["merchant_name"] = merchant_name_row[0]
        except Exception:
            pass
        
        activities.append(session_activity)
    
    # Sort by timestamp (descending) - sessions won't have ts, so they go last
    activities.sort(key=lambda x: x.get("ts", ""), reverse=True)
    
    return {
        "activities": activities[:limit],
        "count": len(activities[:limit])
    }


# ============================================
# Endpoint 6: GET /v1/pilot/app/bootstrap
# ============================================
@router.get("/app/bootstrap")
def bootstrap(
    user_id: Optional[int] = Query(None, description="Optional user ID for balance preload"),
    db: Session = Depends(get_db)
):
    """
    PWA bootstrap endpoint - called on app boot.
    
    Returns hub metadata, chargers, merchant count, and Nova balance.
    Dramatically improves perceived app speed.
    """
    try:
        # Get hub view
        hub_view = get_domain_hub_view(db)
        
        # Shape chargers (no user location for bootstrap)
        shaped_chargers = []
        for charger in hub_view.get("chargers", []):
            shaped = shape_charger(charger)
            shaped_chargers.append(shaped)
        
        # Get merchant count
        merchant_count = len(hub_view.get("merchants", []))
        
        # Get Nova balance if user_id provided
        nova_balance = 0
        if user_id:
            # Get wallet balance (handle case where credit_ledger table doesn't exist yet)
            wallet_balance_cents = 0
            try:
                from app.models_extra import CreditLedger
                ledger_rows = db.query(CreditLedger).filter(CreditLedger.user_ref == str(user_id)).all()
                wallet_balance_cents = sum(r.cents for r in ledger_rows) if ledger_rows else 0
            except Exception as ledger_err:
                # Table might not exist yet - return 0 balance
                logger.warning(f"Could not query wallet balance (table may not exist): {ledger_err}")
                wallet_balance_cents = 0
            nova_balance = cents_to_nova(wallet_balance_cents)
        
        return {
            "pilot_mode": settings.pilot_mode,
            "hub_id": hub_view.get("hub_id", HUB_ID),
            "hub_name": hub_view.get("hub_name", HUB_NAME),
            "chargers": shaped_chargers,
            "merchant_count": merchant_count,
            "nova_balance": nova_balance
        }
    except Exception as e:
        logger.error(f"Failed to bootstrap pilot app: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bootstrap failed: {str(e)}")


# ============================================
# Endpoint 7: GET /v1/pilot/status
# ============================================
@router.get("/status")
def pilot_status(db: Session = Depends(get_db)):
    """
    Pilot mode sanity check endpoint.
    
    Returns pilot configuration and Domain hub seeding status.
    """
    try:
        # Check if Domain is seeded by looking for Domain chargers
        from app.domains.domain_hub import DOMAIN_CHARGERS
        
        domain_seeded = False
        domain_charger_count = 0
        
        try:
            from app.models_while_you_charge import Charger
            charger_ids = [ch["id"] for ch in DOMAIN_CHARGERS]
            domain_charger_count = db.query(Charger).filter(Charger.id.in_(charger_ids)).count()
            domain_seeded = domain_charger_count > 0
        except Exception as e:
            # If Charger model or table doesn't exist, just report not seeded
            logger.debug(f"Could not check charger seeding status: {str(e)}")
            domain_seeded = False
            domain_charger_count = 0
        
        return {
            "pilot_mode": settings.pilot_mode,
            "pilot_hub": settings.pilot_hub,
            "domain_seeded": domain_seeded,
            "domain_charger_count": domain_charger_count
        }
    except Exception as e:
        logger.error(f"Failed to get pilot status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


# ============================================
# Endpoint 8: POST /v1/pilot/merchant_offer
# ============================================
class MerchantOfferRequest(BaseModel):
    """Request model for merchant offer code generation"""
    merchant_id: str
    amount_cents: int


class MerchantOfferResponse(BaseModel):
    """Response model for merchant offer code"""
    code: str
    amount_cents: int
    expires_at: str
    merchant_id: str


@router.post("/merchant_offer", response_model=MerchantOfferResponse)
def create_merchant_offer(
    request: MerchantOfferRequest,
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db)
):
    """
    Generate a unique redemption code for a merchant discount.
    
    Creates a code in the format: PREFIX-MERCHANT-#### (e.g., DOM-SB-4821)
    
    P0-B Security: Requires merchant_admin role and merchant ownership validation.
    """
    # P0-B: Validate merchant ownership - user must own the merchant
    user_merchant = AuthService.get_user_merchant(db, user.id)
    if not user_merchant or user_merchant.id != request.merchant_id:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: You do not have permission to create offers for merchant {request.merchant_id}"
        )
    
    try:
        # Generate unique code
        code = generate_code(request.merchant_id, db)
        
        # Store code with default expiration (30 days)
        offer_code = store_code(
            db=db,
            code=code,
            merchant_id=request.merchant_id,
            amount_cents=request.amount_cents
        )
        
        return MerchantOfferResponse(
            code=offer_code.code,
            amount_cents=offer_code.amount_cents,
            expires_at=offer_code.expires_at.isoformat(),
            merchant_id=offer_code.merchant_id
        )
        
    except ValueError as e:
        logger.error(f"Failed to create merchant offer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create merchant offer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create offer code: {str(e)}")
