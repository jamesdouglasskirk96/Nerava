# app/routers/chargers.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.chargers_openmap import fetch_chargers
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from app.services.google_places_new import _haversine_distance
import math

router = APIRouter()  # main.py mounts with prefix="/v1/chargers"


class NearbyMerchantResponse(BaseModel):
    place_id: str
    name: str
    photo_url: str
    distance_m: float
    walk_time_min: int
    has_exclusive: bool


class DiscoveryChargerResponse(BaseModel):
    id: str
    name: str
    address: str
    lat: float
    lng: float
    distance_m: float
    drive_time_min: int
    network: str
    stalls: int
    kw: float
    photo_url: str
    nearby_merchants: List[NearbyMerchantResponse]


class DiscoveryResponse(BaseModel):
    within_radius: bool
    nearest_charger_id: Optional[str]
    nearest_distance_m: float
    radius_m: int
    chargers: List[DiscoveryChargerResponse]


@router.get("/nearby", response_model=List[Dict[str, Any]])
async def nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(2.0, ge=0.1, le=50.0),
    max_results: int = Query(50, ge=1, le=200)
):
    try:
        items = await fetch_chargers(lat=lat, lng=lng, radius_km=radius_km, max_results=max_results)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"chargers_fetch_failed: {e}")


@router.get("/discovery", response_model=DiscoveryResponse)
async def discovery(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180)
):
    """
    Get charger discovery data with nearby merchants.
    
    Returns chargers sorted by distance, each with 2 nearest merchants.
    Sets within_radius=True if user is within 400m of nearest charger.
    """
    db = SessionLocal()
    try:
        # Query all chargers
        chargers = db.query(Charger).all()
        
        if not chargers:
            return DiscoveryResponse(
                within_radius=False,
                nearest_charger_id=None,
                nearest_distance_m=float('inf'),
                radius_m=400,
                chargers=[]
            )
        
        # Calculate distances and sort
        charger_distances = []
        for charger in chargers:
            distance_m = _haversine_distance(lat, lng, charger.lat, charger.lng)
            charger_distances.append((charger, distance_m))
        
        charger_distances.sort(key=lambda x: x[1])
        
        # Find nearest charger
        nearest_charger, nearest_distance_m = charger_distances[0]
        within_radius = nearest_distance_m <= 400
        
        # Build response for each charger
        discovery_chargers = []
        for charger, distance_m in charger_distances:
            # Calculate drive time (500 m/min, min 1)
            drive_time_min = max(1, math.ceil(distance_m / 500))
            
            # Get 2 nearest merchants
            merchant_links = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger.id
            ).order_by(ChargerMerchant.distance_m.asc()).limit(2).all()
            
            nearby_merchants = []
            for link in merchant_links:
                merchant = db.query(Merchant).filter(Merchant.id == link.merchant_id).first()
                if not merchant:
                    continue
                
                # Calculate walk time (80 m/min, min 1)
                walk_time_min = max(1, math.ceil(link.distance_m / 80))
                
                # Build photo URL - prioritize known merchants with static photos (Asadas Grill)
                merchant_name_lower = merchant.name.lower() if merchant.name else ""
                if "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
                    # Asadas Grill has static photos - use relative path so frontend can prepend API base URL
                    photo_url = "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg"
                elif getattr(merchant, 'primary_photo_url', None):
                    photo_url = merchant.primary_photo_url
                elif merchant.place_id:
                    photo_url = f"/static/demo_chargers/{charger.id}/merchants/{merchant.place_id}_0.jpg"
                else:
                    photo_url = merchant.photo_url or ""
                
                # Check if has exclusive
                has_exclusive = link.exclusive_title is not None and link.exclusive_title != ""
                
                nearby_merchants.append(NearbyMerchantResponse(
                    place_id=merchant.place_id or merchant.id,
                    name=merchant.name,
                    photo_url=photo_url,
                    distance_m=link.distance_m,
                    walk_time_min=walk_time_min,
                    has_exclusive=has_exclusive
                ))
            
            # Build charger photo URL
            charger_photo_url = f"/static/demo_chargers/{charger.id}/hero.jpg"
            
            # Get stalls (use connector_types length as proxy)
            stalls = len(charger.connector_types) if charger.connector_types else 0
            
            discovery_chargers.append(DiscoveryChargerResponse(
                id=charger.id,
                name=charger.name,
                address=charger.address or "",
                lat=charger.lat,
                lng=charger.lng,
                distance_m=distance_m,
                drive_time_min=drive_time_min,
                network=charger.network_name or "Unknown",
                stalls=stalls,
                kw=charger.power_kw or 0.0,
                photo_url=charger_photo_url,
                nearby_merchants=nearby_merchants
            ))
        
        return DiscoveryResponse(
            within_radius=within_radius,
            nearest_charger_id=nearest_charger.id,
            nearest_distance_m=nearest_distance_m,
            radius_m=400,
            chargers=discovery_chargers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"discovery_failed: {e}")
    finally:
        db.close()
