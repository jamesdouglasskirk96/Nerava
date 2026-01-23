"""
Google Places API endpoints for merchant onboarding and enrichment.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies_driver import get_current_driver
from app.services.google_places_new import search_text, place_details
from app.services.merchant_enrichment import enrich_from_google_places
from app.models.while_you_charge import Merchant, ChargerMerchant, Charger

router = APIRouter(prefix="/v1/merchants/places", tags=["places"])


class PlaceSearchResponse(BaseModel):
    place_id: str
    name: str
    lat: float
    lng: float
    address: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    photo_url: Optional[str] = None
    types: List[str] = []


class PlaceDetailsResponse(BaseModel):
    place_id: str
    name: str
    lat: float
    lng: float
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    price_level: Optional[int] = None
    business_status: Optional[str] = None
    types: List[str] = []
    photo_urls: List[str] = []


@router.get("/search", response_model=List[PlaceSearchResponse])
async def search_places(
    q: str = Query(..., description="Search query (e.g., 'Asadas Grill')"),
    lat: Optional[float] = Query(None, description="Latitude for location bias"),
    lng: Optional[float] = Query(None, description="Longitude for location bias"),
    max_results: int = Query(10, ge=1, le=20, description="Maximum number of results"),
):
    """
    Search for places using Google Places API (New) SearchText endpoint.
    Used for merchant onboarding to find and select their business listing.
    """
    location_bias = None
    if lat is not None and lng is not None:
        location_bias = {"lat": lat, "lng": lng}
    
    results = await search_text(q, location_bias=location_bias, max_results=max_results)
    
    # Transform to response format
    response = []
    for result in results:
        # Get photo URL if available
        photo_url = None
        if result.get("photo_url", "").startswith("photo_ref:"):
            from app.services.google_places_new import get_photo_url
            photo_ref = result["photo_url"].replace("photo_ref:", "")
            photo_url = await get_photo_url(photo_ref, max_width=400)
        else:
            photo_url = result.get("photo_url")
        
        response.append(PlaceSearchResponse(
            place_id=result["place_id"],
            name=result["name"],
            lat=result["lat"],
            lng=result["lng"],
            address=None,  # Not in search results
            rating=result.get("rating"),
            user_rating_count=result.get("user_rating_count"),
            photo_url=photo_url,
            types=result.get("types", []),
        ))
    
    return response


@router.get("/{place_id}", response_model=PlaceDetailsResponse)
async def get_place_details(place_id: str):
    """
    Get full place details for a given Google Places ID.
    Used to fetch complete information before creating a merchant record.
    """
    place_data = await place_details(place_id)
    
    if not place_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place '{place_id}' not found"
        )
    
    # Extract data
    display_name = place_data.get("displayName", {})
    name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
    location = place_data.get("location", {})
    
    # Get photo URLs
    photo_urls = []
    photos = place_data.get("photos", [])
    for photo in photos[:5]:  # Limit to 5 photos
        photo_name = photo.get("name", "")
        if photo_name:
            from app.services.google_places_new import get_photo_url
            photo_ref = photo_name.replace("places/", "").split("/photos/")[-1]
            if photo_ref:
                photo_url = await get_photo_url(photo_ref, max_width=800)
                if photo_url:
                    photo_urls.append(photo_url)
    
    return PlaceDetailsResponse(
        place_id=place_id.replace("places/", ""),
        name=name,
        lat=location.get("latitude", 0),
        lng=location.get("longitude", 0),
        address=place_data.get("formattedAddress"),
        phone=place_data.get("nationalPhoneNumber"),
        website=place_data.get("websiteUri"),
        rating=place_data.get("rating"),
        user_rating_count=place_data.get("userRatingCount"),
        price_level=place_data.get("priceLevel"),
        business_status=place_data.get("businessStatus"),
        types=place_data.get("types", []),
        photo_urls=photo_urls,
    )


@router.post("/merchants/{merchant_id}/refresh")
async def refresh_merchant_from_places(
    merchant_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_driver),  # Require auth
):
    """
    Refresh merchant data from Google Places API.
    Rate-limited: max 1 refresh per day per merchant.
    """
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant '{merchant_id}' not found"
        )
    
    if not merchant.place_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Merchant does not have a place_id"
        )
    
    # Check rate limit (simple check - in production, use Redis)
    from datetime import datetime, timedelta
    if merchant.google_places_updated_at:
        age = datetime.utcnow() - merchant.google_places_updated_at
        if age < timedelta(hours=24):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Merchant was refreshed less than 24 hours ago"
            )
    
    # Enrich merchant
    success = await enrich_from_google_places(db, merchant, merchant.place_id, force_refresh=True)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh merchant data"
        )
    
    return {"status": "success", "merchant_id": merchant_id}
