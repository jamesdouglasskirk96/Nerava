# app/routers/chargers.py
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.chargers_openmap import fetch_chargers
from app.db import get_db
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant, MerchantPerk
from app.services.google_places_new import _haversine_distance
import math

router = APIRouter()  # main.py mounts with prefix="/v1/chargers"

# Fallback photo URLs by network type (Unsplash images)
FALLBACK_CHARGER_PHOTOS = {
    "Tesla": "https://images.unsplash.com/photo-1593941707882-a5bac6861d75?w=800&q=80",
    "ChargePoint": "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?w=800&q=80",
    "EVgo": "https://images.unsplash.com/photo-1647166545674-ce28ce93bdca?w=800&q=80",
    "default": "https://images.unsplash.com/photo-1620714223084-8fcacc6dfd8d?w=800&q=80",
}


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
async def get_charger_discovery(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    search: Optional[str] = Query(None, description="Search for chargers by merchant name"),
    db: Session = Depends(get_db),
):
    """
    Get charger discovery data with nearby merchants.

    Returns ALL chargers sorted by:
    1. Has exclusive merchants (descending)
    2. Distance from user (ascending)
    """
    try:
        # Get ALL chargers (no distance limit)
        chargers = db.query(Charger).all()

        if not chargers:
            return DiscoveryResponse(
                within_radius=False,
                nearest_charger_id=None,
                nearest_distance_m=0,
                radius_m=0,
                chargers=[]
            )

        # If search is provided, filter chargers by merchant name
        if search and search.strip():
            search_term = search.strip().lower()
            matching_charger_ids = set()
            
            # Find merchants matching the search term
            matching_merchants = db.query(Merchant).filter(
                Merchant.name.ilike(f"%{search_term}%")
            ).all()
            
            # Find chargers linked to these merchants
            for merchant in matching_merchants:
                charger_merchants = db.query(ChargerMerchant).filter(
                    ChargerMerchant.merchant_id == merchant.id
                ).all()
                for cm in charger_merchants:
                    matching_charger_ids.add(cm.charger_id)
            
            # Filter chargers to only those matching
            chargers = [c for c in chargers if c.id in matching_charger_ids]
            
            if not chargers:
                return DiscoveryResponse(
                    within_radius=False,
                    nearest_charger_id=None,
                    nearest_distance_m=float('inf'),
                    radius_m=0,
                    chargers=[]
                )

        # Calculate distance for each charger and check for exclusives
        charger_with_data = []
        for charger in chargers:
            distance_m = _haversine_distance(lat, lng, charger.lat, charger.lng)

            # Get nearby merchants for this charger via ChargerMerchant links
            merchant_links = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger.id
            ).order_by(ChargerMerchant.distance_m.asc()).limit(2).all()

            # Check if any merchant has exclusive
            has_exclusive = False
            nearby_merchants_list = []
            
            for link in merchant_links:
                merchant = db.query(Merchant).filter(Merchant.id == link.merchant_id).first()
                if not merchant:
                    continue
                
                # Check if merchant has exclusive
                merchant_has_exclusive = False
                merchant_perk = db.query(MerchantPerk).filter(
                    MerchantPerk.merchant_id == merchant.id,
                    MerchantPerk.is_active == True
                ).first()
                if merchant_perk:
                    merchant_has_exclusive = True
                elif hasattr(link, 'exclusive_title') and link.exclusive_title:
                    merchant_has_exclusive = True
                else:
                    merchant_name_lower = merchant.name.lower() if merchant.name else ""
                    if "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
                        merchant_has_exclusive = True
                
                if merchant_has_exclusive:
                    has_exclusive = True
                
                # Calculate walk time (80 m/min, min 1)
                walk_time_min = max(1, math.ceil(link.distance_m / 80))
                
                # Build photo URL - prioritize database values over static paths
                merchant_name_lower = merchant.name.lower() if merchant.name else ""
                if merchant.photo_url and merchant.photo_url.strip():
                    photo_url = merchant.photo_url
                elif getattr(merchant, 'primary_photo_url', None):
                    photo_url = merchant.primary_photo_url
                elif "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
                    photo_url = "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg"
                elif merchant.external_id:
                    photo_url = f"/static/demo_chargers/{charger.id}/merchants/{merchant.external_id}_0.jpg"
                else:
                    photo_url = ""
                
                # Use external_id (Google Places ID) as place_id, fallback to merchant.id
                place_id = merchant.external_id or merchant.id
                
                nearby_merchants_list.append(NearbyMerchantResponse(
                    place_id=place_id,
                    name=merchant.name,
                    photo_url=photo_url,
                    distance_m=link.distance_m,
                    walk_time_min=walk_time_min,
                    has_exclusive=merchant_has_exclusive
                ))

            # Calculate drive time (500 m/min, min 1)
            drive_time_min = max(1, math.ceil(distance_m / 500))

            # Get stalls count
            stalls = len(charger.connector_types) if charger.connector_types else 1

            # Build charger photo URL with fallback logic
            charger_photo_url = getattr(charger, 'photo_url', None)
            if not charger_photo_url or charger_photo_url.startswith("/static/"):
                # Use fallback based on network type
                charger_photo_url = FALLBACK_CHARGER_PHOTOS.get(
                    charger.network_name or "",
                    FALLBACK_CHARGER_PHOTOS["default"]
                )

            charger_with_data.append({
                "response": DiscoveryChargerResponse(
                    id=charger.id,
                    name=charger.name,
                    address=charger.address or "",
                    lat=charger.lat,
                    lng=charger.lng,
                    distance_m=distance_m,
                    drive_time_min=drive_time_min,
                    network=charger.network_name or "Unknown",
                    stalls=stalls,
                    kw=charger.power_kw or 0,
                    photo_url=charger_photo_url,
                    nearby_merchants=nearby_merchants_list
                ),
                "has_exclusive": has_exclusive,
                "distance_m": distance_m
            })

        # SORT: exclusives first, then by distance
        charger_with_data.sort(key=lambda x: (not x["has_exclusive"], x["distance_m"]))

        # Extract sorted charger responses
        sorted_chargers = [c["response"] for c in charger_with_data]

        # Find nearest charger for within_radius check
        if charger_with_data:
            nearest_distance_m = min(c["distance_m"] for c in charger_with_data)
            nearest_charger_id = next(c["response"].id for c in charger_with_data if c["distance_m"] == nearest_distance_m)
            within_radius = nearest_distance_m <= 400
        else:
            nearest_distance_m = float('inf')
            nearest_charger_id = None
            within_radius = False

        return DiscoveryResponse(
            within_radius=within_radius,
            nearest_charger_id=nearest_charger_id,
            nearest_distance_m=nearest_distance_m,
            radius_m=0,  # No radius limit - show all
            chargers=sorted_chargers
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"discovery_failed: {e}")
