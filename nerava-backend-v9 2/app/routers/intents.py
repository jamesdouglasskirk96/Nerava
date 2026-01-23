from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
import uuid
import math

router = APIRouter()

def km_distance(p1, p2):
    """Calculate distance between two lat/lng points in kilometers"""
    R = 6371  # Earth's radius in km
    to_rad = lambda d: d * math.pi / 180
    d_lat = to_rad(p2['lat'] - p1['lat'])
    d_lng = to_rad(p2['lng'] - p1['lng'])
    a = math.sin(d_lat/2)**2 + math.cos(to_rad(p1['lat'])) * math.cos(to_rad(p2['lat'])) * math.sin(d_lng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@router.get("/v1/intent")
async def get_intent(db: Session = Depends(get_db)):
    """Get saved intents for the user"""
    try:
        me = "demo-user-123"
        
        # Check if table exists first
        check_table = text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='charge_intents'
        """)
        table_exists = db.execute(check_table).fetchone()
        
        if not table_exists:
            # Table doesn't exist, return empty list
            return []
        
        query = text("""
            SELECT * FROM charge_intents 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        
        result = db.execute(query, {'user_id': me})
        intents = []
        
        for row in result:
            # Helper to safely get datetime or string
            def safe_datetime(idx):
                if len(row) <= idx or row[idx] is None:
                    return None
                val = row[idx]
                # If it's already a string, return it
                if isinstance(val, str):
                    return val
                # If it's a datetime object, convert to ISO
                if hasattr(val, 'isoformat'):
                    return val.isoformat()
                return str(val)
            
            intents.append({
                'id': row[0] if len(row) > 0 else None,
                'user_id': row[1] if len(row) > 1 else None,
                'station_id': row[2] if len(row) > 2 else None,
                'station_name': row[3] if len(row) > 3 else None,
                'merchant_name': row[4] if len(row) > 4 else None,
                'perk_title': row[5] if len(row) > 5 else None,
                'address': row[6] if len(row) > 6 else None,
                'eta_minutes': row[7] if len(row) > 7 else None,
                'starts_at': safe_datetime(8),
                'status': row[9] if len(row) > 9 else 'saved',
                'merchant_lat': row[10] if len(row) > 10 else None,
                'merchant_lng': row[11] if len(row) > 11 else None,
                'station_lat': row[12] if len(row) > 12 else None,
                'station_lng': row[13] if len(row) > 13 else None,
                'merchant': row[16] if len(row) > 16 else None,  # New field
                'perk_id': row[17] if len(row) > 17 else None,   # New field
                'window_text': row[18] if len(row) > 18 else None,  # New field
                'distance_text': row[19] if len(row) > 19 else None,  # New field
                'created_at': safe_datetime(14)
            })
        
        return intents
    except Exception as e:
        # Log error but return empty list instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error fetching intents: {e}", exc_info=True)
        # Return empty list so frontend doesn't crash
        return []

@router.post("/v1/intent")
async def create_intent(payload: dict, db: Session = Depends(get_db)):
    """Save a perk/station combo for later activation on Earn page"""
    me = "demo-user-123"
    
    station_id = payload.get("station_id")
    merchant = payload.get("merchant")
    perk_id = payload.get("perk_id")
    station_name = payload.get("station_name")
    address = payload.get("address")
    window_text = payload.get("window_text")
    distance_text = payload.get("distance_text")
    
    # Simple dedupe (optional):
    recent_query = text("""
      SELECT id FROM charge_intents
      WHERE user_id=:uid AND status='saved'
        AND COALESCE(merchant,'') = COALESCE(:merchant,'')
        AND COALESCE(station_id,'') = COALESCE(:station_id,'')
        AND created_at >= DATETIME('now','-10 minutes')
      ORDER BY created_at DESC LIMIT 1
    """)
    recent = db.execute(recent_query, {'uid': me, 'merchant': merchant, 'station_id': station_id}).first()
    if recent:
        return {"ok": True, "id": recent[0], "deduped": True}
    
    iid = str(uuid.uuid4())
    insert_query = text("""
        INSERT INTO charge_intents 
        (id, user_id, station_id, station_name, merchant, address, window_text, distance_text, perk_id, status)
        VALUES (:id, :user_id, :station_id, :station_name, :merchant, :address, :window_text, :distance_text, :perk_id, :status)
    """)
    
    db.execute(insert_query, {
        'id': iid,
        'user_id': me,
        'station_id': station_id,
        'station_name': station_name,
        'merchant': merchant,
        'address': address,
        'window_text': window_text,
        'distance_text': distance_text,
        'perk_id': perk_id,
        'status': 'saved'
    })
    db.commit()
    return {"ok": True, "id": iid}

@router.post("/v1/intents")
async def save_intent(intent_data: dict, db: Session = Depends(get_db)):
    """Save a charge intent"""
    # For demo purposes, use hardcoded user ID
    me = "demo-user-123"
    
    intent_id = str(uuid.uuid4())
    
    query = text("""
        INSERT INTO charge_intents 
        (id, user_id, station_id, station_name, merchant_name, perk_title, address, eta_minutes,
         merchant_lat, merchant_lng, station_lat, station_lng)
        VALUES (:id, :user_id, :station_id, :station_name, :merchant_name, :perk_title, :address, :eta_minutes,
                :merchant_lat, :merchant_lng, :station_lat, :station_lng)
    """)
    
    db.execute(query, {
        'id': intent_id,
        'user_id': me,
        'station_id': intent_data.get('stationId'),
        'station_name': intent_data.get('stationName'),
        'merchant_name': intent_data.get('merchantName'),
        'perk_title': intent_data.get('perkTitle'),
        'address': intent_data.get('address'),
        'eta_minutes': intent_data.get('etaMinutes'),
        'merchant_lat': intent_data.get('merchantLat'),
        'merchant_lng': intent_data.get('merchantLng'),
        'station_lat': intent_data.get('stationLat'),
        'station_lng': intent_data.get('stationLng')
    })
    
    db.commit()
    return {"ok": True, "id": intent_id}

@router.get("/v1/intents/me")
async def get_my_intents(db: Session = Depends(get_db)):
    """Get my open intents"""
    me = "demo-user-123"
    
    query = text("""
        SELECT * FROM charge_intents 
        WHERE user_id = :user_id AND status IN ('saved', 'started')
        ORDER BY created_at DESC
    """)
    
    result = db.execute(query, {'user_id': me})
    intents = []
    
    for row in result:
        intents.append({
            'id': row[0],
            'user_id': row[1],
            'station_id': row[2],
            'station_name': row[3],
            'merchant_name': row[4],
            'perk_title': row[5],
            'address': row[6],
            'eta_minutes': row[7],
            'starts_at': row[8],
            'status': row[9],
            'merchant_lat': row[10],
            'merchant_lng': row[11],
            'station_lat': row[12],
            'station_lng': row[13],
            'created_at': row[14],
            'updated_at': row[15]
        })
    
    return intents

@router.patch("/v1/intents/{intent_id}/start")
async def start_intent(intent_id: str, db: Session = Depends(get_db)):
    """Start an intent"""
    me = "demo-user-123"
    
    query = text("""
        UPDATE charge_intents
        SET status = 'started', starts_at = now(), updated_at = now()
        WHERE id = :id AND user_id = :user_id AND status = 'saved'
        RETURNING *
    """)
    
    result = db.execute(query, {'id': intent_id, 'user_id': me})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    db.commit()
    
    return {
        "ok": True,
        "zones": {
            "station": {"lat": row[12], "lng": row[13], "radius_m": 120},
            "merchant": {"lat": row[10], "lng": row[11], "radius_m": 120}
        },
        "policy": {"require_both": True, "within_minutes": 60}
    }

@router.post("/v1/intents/{intent_id}/verify-geo")
async def verify_geo(intent_id: str, geo_data: dict, db: Session = Depends(get_db)):
    """Verify dual-zone geo location"""
    me = "demo-user-123"
    
    # Get intent
    query = text("SELECT * FROM charge_intents WHERE id = :id AND user_id = :user_id")
    result = db.execute(query, {'id': intent_id, 'user_id': me})
    intent = result.fetchone()
    
    if not intent:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check distances
    here = {'lat': float(geo_data['lat']), 'lng': float(geo_data['lng'])}
    station = {'lat': intent[12], 'lng': intent[13]}
    merchant = {'lat': intent[10], 'lng': intent[11]}
    
    near_station = km_distance(here, station) * 1000 <= 150  # 150m
    near_merchant = km_distance(here, merchant) * 1000 <= 150  # 150m
    
    pass_verification = near_station and near_merchant
    
    if pass_verification:
        update_query = text("""
            UPDATE charge_intents 
            SET status = 'completed', updated_at = now() 
            WHERE id = :id
        """)
        db.execute(update_query, {'id': intent_id})
        db.commit()
    
    return {
        "ok": True,
        "pass": pass_verification,
        "nearStation": near_station,
        "nearMerchant": near_merchant,
        "status": "completed" if pass_verification else intent[9]
    }
