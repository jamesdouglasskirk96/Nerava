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
